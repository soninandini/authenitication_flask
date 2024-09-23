
from flask import Blueprint, request, jsonify
from models import db, User, Contact
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import asc, desc
import re

app = Blueprint('routes', __name__)

EMAIL_REGEX = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

@app.route('/user/signup', methods=['POST'])
def signup():
    data = request.get_json()

   
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name:
        return jsonify({"message": "Name cannot be left blank", "data": {}}), 400

    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({"message": "Email is not valid", "data": {}}), 400
    
    if not password or not re.match(PASSWORD_REGEX, password):
        return jsonify({
            "message": "Password must be at least 8 characters long, include at least one uppercase letter, and one special character",
            "data": {}
        }), 400

    if not password:
        return jsonify({"message": "Password cannot be left blank", "data": {}}), 400

   
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered", "data": {}}), 400

   
    new_user = User(name=name, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    
    access_token = create_access_token(identity=new_user.id)

    return jsonify({
        "message": "User signup complete",
        "data": {
            "access_token": access_token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }
    }), 200



@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()

   
    email = data.get('email')
    password = data.get('password')

    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({"message": "Email is not valid", "data": {}}), 400

    if not password:
        return jsonify({"message": "Password cannot be left blank", "data": {}}), 400

   
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Email not registered", "data": {}}), 400

   
    if not user.check_password(password):
        return jsonify({"message": "Invalid credentials", "data": {}}), 401

   
    access_token = create_access_token(identity=user.id)

    return jsonify({
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    }), 200



@app.route('/user', methods=['GET'])
@jwt_required()
def get_user_details():
    current_user_id = get_jwt_identity()

   
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found", "data": {}}), 404

    return jsonify({
        "message": "User detail",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200



@app.route('/contact', methods=['POST'])
@jwt_required()
def add_contact():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')
    country = data.get('country')

   
    if not name:
        return jsonify({"message": "Name is required", "data": {}}), 400

    if not phone:
        return jsonify({"message": "Phone is required", "data": {}}), 400

    if email and not re.match(EMAIL_REGEX, email):
        return jsonify({"message": "Email is not valid", "data": {}}), 400


    new_contact = Contact(
        name=name,
        phone=phone,
        email=email,
        address=address,
        country=country,
        user_id=current_user_id
    )
    db.session.add(new_contact)
    db.session.commit()

    return jsonify({
        "message": "Contact added",
        "data": {
            "id": new_contact.id,
            "name": new_contact.name,
            "email": new_contact.email,
            "phone": new_contact.phone,
            "address": new_contact.address,
            "country": new_contact.country
        }
    }), 200

@app.route('/contact', methods=['GET'])
@jwt_required()
def list_contacts():
    current_user_id = get_jwt_identity()
    
  
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    

    sort_by = request.args.get('sort_by', 'latest')

  
    name = request.args.get('name', type=str)
    email = request.args.get('email', type=str)
    phone = request.args.get('phone', type=str)
    
  
    query = Contact.query.filter_by(user_id=current_user_id)

    if name:
        query = query.filter(Contact.name.ilike(f"%{name}%"))
    
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    
    if phone:
        query = query.filter(Contact.phone.ilike(f"%{phone}%"))
   
    if sort_by == 'latest':
        query = query.order_by(desc(Contact.id))
    elif sort_by == 'oldest':
        query = query.order_by(asc(Contact.id))
    elif sort_by == 'alphabetically_a_to_z':
        query = query.order_by(asc(Contact.name))
    elif sort_by == 'alphabetically_z_to_a':
        query = query.order_by(desc(Contact.name))
    
   
    paginated_contacts = query.paginate(page=page, per_page=limit, error_out=False)
    
    contacts_list = [{
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone,
        "address": contact.address,
        "country": contact.country
    } for contact in paginated_contacts.items]

    return jsonify({
        "message": "Contact list",
        "data": {
            "list": contacts_list,
            "has_next": paginated_contacts.has_next,
            "has_prev": paginated_contacts.has_prev,
            "page": paginated_contacts.page,
            "pages": paginated_contacts.pages,
            "per_page": paginated_contacts.per_page,
            "total": paginated_contacts.total
        }
    }), 200