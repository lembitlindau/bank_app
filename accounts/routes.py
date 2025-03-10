from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
from .. import db
from ..models import Account, Transaction, BankSettings
from . import accounts_bp
from .forms import CreateAccountForm, TransferForm

@accounts_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing all accounts and recent transactions."""
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Get recent transactions for all user accounts
    recent_transactions = []
    for account in accounts:
        sent = Transaction.query.filter_by(account_from_id=account.id).order_by(Transaction.created_at.desc()).limit(5).all()
        received = Transaction.query.filter_by(account_to_id=account.id).order_by(Transaction.created_at.desc()).limit(5).all()
        recent_transactions.extend(sent + received)
    
    # Sort transactions by date (newest first)
    recent_transactions.sort(key=lambda x: x.created_at, reverse=True)
    recent_transactions = recent_transactions[:10]  # Limit to 10 most recent
    
    return render_template('accounts/dashboard.html', 
                           title='Dashboard', 
                           accounts=accounts, 
                           transactions=recent_transactions)

@accounts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_account():
    """Create a new bank account."""
    form = CreateAccountForm()
    if form.validate_on_submit():
        # Get bank settings for the prefix
        bank_settings = BankSettings.query.first()
        if not bank_settings:
            flash('Bank not properly configured. Please contact an administrator.')
            return redirect(url_for('accounts.dashboard'))
        
        # Generate account number with bank prefix
        account_number = Account.generate_account_number(bank_settings.bank_prefix)
        
        # Create the account
        account = Account(
            account_number=account_number,
            user_id=current_user.id,
            balance=form.initial_deposit.data,
            currency=form.currency.data
        )
        db.session.add(account)
        db.session.commit()
        
        flash(f'Account {account_number} created successfully!')
        return redirect(url_for('accounts.dashboard'))
    
    return render_template('accounts/create_account.html', 
                           title='Create Account', 
                           form=form)

@accounts_bp.route('/details/<account_number>')
@login_required
def account_details(account_number):
    """View detailed account information and transaction history."""
    account = Account.query.filter_by(account_number=account_number).first_or_404()
    
    # Ensure the user owns this account
    if account.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this account.')
        return redirect(url_for('accounts.dashboard'))
    
    # Get all transactions for this account
    sent_transactions = Transaction.query.filter_by(account_from_id=account.id).order_by(Transaction.created_at.desc()).all()
    received_transactions = Transaction.query.filter_by(account_to_id=account.id).order_by(Transaction.created_at.desc()).all()
    
    # Combine and sort transactions
    transactions = sorted(sent_transactions + received_transactions, 
                          key=lambda x: x.created_at, 
                          reverse=True)
    
    return render_template('accounts/account_details.html', 
                           title=f'Account {account_number}', 
                           account=account, 
                           transactions=transactions)

@accounts_bp.route('/transfer/<account_number>', methods=['GET', 'POST'])
@login_required
def transfer(account_number):
    """Transfer money to another account (internal or external)."""
    account = Account.query.filter_by(account_number=account_number).first_or_404()
    
    # Ensure the user owns this account
    if account.user_id != current_user.id:
        flash('You do not have permission to transfer from this account.')
        return redirect(url_for('accounts.dashboard'))
    
    form = TransferForm()
    if form.validate_on_submit():
        # Check if sufficient funds
        if account.balance < form.amount.data:
            flash('Insufficient funds for this transfer.')
            return redirect(url_for('accounts.transfer', account_number=account_number))
        
        # Get the destination account number
        destination_account_number = form.account_to.data
        
        # Get bank settings for the prefix
        bank_settings = BankSettings.query.first()
        if not bank_settings:
            flash('Bank not properly configured. Please contact an administrator.')
            return redirect(url_for('accounts.dashboard'))
        
        # Check if internal or external transfer
        if destination_account_number.startswith(bank_settings.bank_prefix):
            # Internal transfer
            destination_account = Account.query.filter_by(account_number=destination_account_number).first()
            if not destination_account:
                flash('Destination account not found.')
                return redirect(url_for('accounts.transfer', account_number=account_number))
            
            # Create transaction
            transaction = Transaction(
                transaction_id=Transaction.generate_transaction_id(),
                account_from_id=account.id,
                account_to_id=destination_account.id,
                amount=form.amount.data,
                currency=account.currency,
                explanation=form.explanation.data,
                status='completed',
                is_internal=True,
                completed_at=datetime.utcnow(),
                receiver_name=destination_account.owner.full_name
            )
            
            # Update account balances
            account.balance -= form.amount.data
            destination_account.balance += form.amount.data
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Transfer completed successfully!')
        else:
            # External transfer
            from ..utils.transaction_handler import process_outgoing_transaction
            
            result = process_outgoing_transaction(
                account_from=account,
                account_to=destination_account_number,
                amount=form.amount.data,
                currency=account.currency,
                explanation=form.explanation.data,
                sender_name=current_user.full_name
            )
            
            if result.get('success'):
                flash(f'Transfer to {result.get("receiver_name")} completed successfully!')
            else:
                flash(f'Transfer failed: {result.get("error")}')
        
        return redirect(url_for('accounts.account_details', account_number=account_number))
    
    return render_template('accounts/transfer.html', 
                           title='Transfer Money', 
                           account=account, 
                           form=form)
