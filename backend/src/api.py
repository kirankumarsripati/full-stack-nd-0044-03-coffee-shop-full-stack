import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks_query = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks_query]
    })


'''
DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(payload):
    drinks_query = Drink.query.all()

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks_query]
    })


'''
DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    if not body:
        abort(422, {'message': 'invalid body JSON'})

    new_drink = body.get('title', None)
    new_recipe = body.get('recipe', None)

    if not new_drink:
        abort(422, {'message': '{} cannot be blank'.format('drink')})

    if not new_recipe:
        abort(422, {'message': '{} cannot be blank'.format('recipe')})

    try:
        drink = Drink(
            title=new_drink,
            recipe=json.dumps(new_recipe)
        )
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(404, description={'message': 'failed to add a drink'})


'''
DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()

    if not body:
        abort(422, description={'message': 'invalid body JSON'})

    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if not drink:
        abort(404, description={'message': 'drinks not found'})

    title = body.get('title', None)
    recipe = body.get('recipe', None)

    try:
        if title:
            drink.title = title
        if recipe:
            drink.recipe = json.dumps(recipe)
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(422)


'''
DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    drink = Drink.query.get(drink_id)

    if not drink:
        abort(404, description={'message': 'drinks not found'})

    try:
        drink.delete()

        return jsonify({
            'success': True,
            'deleted': drink_id
        })
    except Exception:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': get_error_message(error, 'unprocessable')
    }), 422


'''
DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
DONE implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': get_error_message(error, 'resource not found')
    }), 404


def get_error_message(error, default_message):
    '''
    Returns if there is any error message provided in
    error.description.message else default_message
    This can be passed by calling
    abort(404, description={'message': 'your message'})

    Parameters:
    error (werkzeug.exceptions.NotFound): error object
    default_message (str): default message if custom message not available

    Returns:
    str: Custom error message or default error message
    '''
    try:
        return error.description['message']
    except TypeError:
        return default_message


'''
DONE implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(e):
    return jsonify({
        'success': False,
        'error': e.status_code,
        'message': e.error
    }), 401
