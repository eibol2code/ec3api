#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request
import subprocess
import tempfile
import os
import json, sys
import os.path

app = Flask(__name__)

# Combination of chars used to separate the lines in the AUTH header
AUTH_LINE_SEPARATOR = '\\n'
# Combination of chars used to separate the lines inside the auth data
# (i.e. in a certificate)
AUTH_NEW_LINE_SEPARATOR = '\\\\n'

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

# ------------------------ TEMPLATES ------------------------------------------------#
# DELETE a custom template
@app.route('/todo/api/v2.0/templates/<string:template_name>', methods=['DELETE'])
def delete_templates(template_name):
    # Ruta de los custom templates 
    ruta = '/ec3/custom_templates/' + template_name + '.radl'
    
    # Borramos si el existe el template y es un fichero
    if not os.path.exists(ruta):
        abort(404)
    elif os.path.isfile(ruta):
        os.remove(ruta)
        return '200'
    else:    ## Show an error ##
        return '400'

# POST a custom template
@app.route('/todo/api/v2.0/templates', methods=['POST'])
def post_templates():
    f = request.files['files']
    nombre_fichero = f.filename
    ruta = '/ec3/custom_templates/' + nombre_fichero
    f.save(ruta)
    return '200'

#GET a template
@app.route('/todo/api/v2.0/templates', methods=['GET'])
def templates():

    ruta_ec3 = "/ec3/ec3 "
    orden = "templates "

    if request.json:
        if 'nombre' in request.json:
            nombre = request.json['nombre']
            comando = ruta_ec3 + orden + "-n " + nombre + " --json"
            proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE)
            respuesta = proceso.stdout.read()
            proceso.wait()
            return respuesta

        if 'pattern' in request.json:            
            pattern = request.json['pattern']
            comando = ruta_ec3 + orden + "-s " + pattern + " --json"
            proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE)
            respuesta = proceso.stdout.read()
            proceso.wait()
            return respuesta
         
        abort(400)
    
    if not request.json:        	
        comando = ruta_ec3 + orden
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE)
        respuesta = proceso.stdout.read()
        proceso.wait()
        return respuesta

# ------------------------ CLUSTERS ------------------------------------------------#
#POST launch a cluster
@app.route('/todo/api/v2.0/clusters', methods=['POST'])
def create_cluster():

    if not request.json or not 'clustername' in request.json:
        abort(400)

    # Task retrieving the info from the API request
    task = {
        'clustername': request.json['clustername'],
        'templates': request.json['templates'],
    }

    # Getting all the templates going to be used in a string
    templates = ''
    for template in task['templates']:
        templates += task['templates'][template] + ' '
    
    # Making a temporary file for the auth
    # Getting info from the headers
    auth_data = request.headers['AUTHORIZATION'].replace(AUTH_NEW_LINE_SEPARATOR, "\n")
    auth_data = auth_data.split(AUTH_LINE_SEPARATOR)

    (fd, filename) = tempfile.mkstemp(dir='/ec3')
    tfile = os.fdopen(fd, "w")
    for auth in auth_data:
        tfile.write(auth)
        tfile.write('\n')

    tfile.close()

    # Formatting other parameters
    ruta_ec3 = "/ec3/ec3 "
    orden = "launch "
    nombre_cluster = task['clustername']
    
    # Making the final command to launch
    comando = ruta_ec3 + orden + nombre_cluster + " " + templates + " -a " + filename + " -y"

    # Launching the process
    proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE)
    respuesta = proceso.stdout.read()
    proceso.wait()

    # Removing the temporary file
    os.remove(filename)

    return respuesta

# GET all clusters info
@app.route('/todo/api/v2.0/clusters', methods=['GET'])
def get_clusters():
    output = subprocess.Popen("/ec3/ec3 list -r --json", shell=True, stdout=subprocess.PIPE).stdout.read()
    return output

# GET specific cluster info
@app.route('/todo/api/v2.0/clusters/<string:cluster_name>', methods=['GET'])
def get_cluster(cluster_name):
    output = subprocess.Popen("/ec3/ec3 show " + cluster_name + " --json", shell=True, stdout=subprocess.PIPE).stdout.read()
    return output

# DELETE removing specific cluster
@app.route('/todo/api/v2.0/clusters/<string:cluster_name>', methods=['DELETE'])
def delete_cluster(cluster_name):
    proc = subprocess.Popen("/ec3/ec3 destroy " + cluster_name + " --force", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output = proc.communicate("y")
    return output

# UPDATE cluster
@app.route('/todo/api/v2.0/clusters/<string:cluster_name>', methods=['POST'])
def update_cluster(cluster_name):
    parameters = request.json['parameters']
    print(parameters)

    output = subprocess.Popen("/ec3/ec3 reconfigure " + cluster_name + " --add \"" + parameters + "\"", shell=True, stdout=subprocess.PIPE).stdout.read()
    return output

###########################################################################################################

if __name__ == '__main__':
    app.run(debug=True)

