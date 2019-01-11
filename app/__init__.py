from flask import Flask
webapp = Flask(__name__)

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'

from app import SignIn
from app import SignUp
from app import LogOut
from app import dynamodb
from app import s3
from app import UserHomePage_Upload
from app import Community