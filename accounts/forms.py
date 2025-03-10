from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError
from ..models import Account

class CreateAccountForm(FlaskForm):
    """Form for creating a new bank account."""
    currency = SelectField('Currency', 
                          choices=[('EUR', 'Euro (EUR)'), 
                                   ('USD', 'US Dollar (USD)'), 
                                   ('GBP', 'British Pound (GBP)')],
                          validators=[DataRequired()])
    initial_deposit = DecimalField('Initial Deposit', 
                                  validators=[DataRequired(), 
                                             NumberRange(min=0, message='Initial deposit must be positive')])
    submit = SubmitField('Create Account')

class TransferForm(FlaskForm):
    """Form for transferring money between accounts."""
    account_to = StringField('Destination Account Number', 
                            validators=[DataRequired(), 
                                       Length(min=3, max=64)])
    amount = DecimalField('Amount', 
                         validators=[DataRequired(), 
                                    NumberRange(min=0.01, message='Amount must be positive')])
    explanation = TextAreaField('Explanation', 
                               validators=[DataRequired(), 
                                          Length(max=256)])
    submit = SubmitField('Transfer')
