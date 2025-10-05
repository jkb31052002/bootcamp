from flask import Flask, render_template, request, url_for, session, flash, abort, redirect
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from flask import current_app as app
from datetime import datetime, date
from .models import *

#HOME PAGE
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

#ADMIN LOGIN
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwd = request.form.get('pwd')
        this_admin = Admin.query.filter_by(username=u_name).first()
        if not this_admin:
            return render_template('admin_login.html', error="Admin does not exist")
        if this_admin.password != pwd:
            return render_template('admin_login.html', error="Incorrect password")
        
        login_user(this_admin)
        #add features of dashboard

        return render_template('admin_dashboard.html', current_user=this_admin, u_name=u_name)
    return render_template('admin_login.html')


#SPONSOR REGISTER
@app.route('/sponsorregister', methods=['GET', 'POST'])
def sponsor_reg():
    if request.method =='POST':
        u_name = request.form.get('u_name')
        pwd = request.form.get('pwd')
        c_name = request.form.get('c_name')
        c_budget = request.form.get('c_budget')
        industry = request.form.get('industry')
        # if c_budget < 0:
            # return render_template('sponsor_register.html', message="Budget must be greater than 0")
        if not (u_name and pwd and c_name and c_budget and industry):
            return render_template('sponsor_register.html', message="Please fill out all fields")
        this_sponsor = Sponsor.query.filter_by(username=u_name).first()
        if this_sponsor:
            return render_template('sponsor_register.html', message="Username already exists")
        
        else:
            new_user = User(username=u_name, user_role=1)
            db.session.add(new_user)
            db.session.commit()

            new_sponsor = Sponsor(username=u_name, password=pwd, company_name=c_name, company_budget=c_budget, industry=industry, sponsor_id=new_user.id)
            db.session.add(new_sponsor)
            db.session.commit()

            return redirect('/sponsorlogin')
    return render_template('sponsor_register.html')

#SPONSOR LOGIN
@app.route('/sponsorlogin', methods=['GET', 'POST'])
def sponsor_login():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        pwd = request.form.get('pwd')
        this_sponsor = User.query.filter_by(username=u_name).first()
        if not this_sponsor:
            return render_template('sponsor_login.html', error="User does not exist")
        if this_sponsor:
            sponsor = Sponsor.query.filter_by(sponsor_id=this_sponsor.id).first()
            if sponsor.password != pwd:
                return render_template('sponsor_login.html', error="Incorrect password")
            else:
                if sponsor.flagged == 1:
                    return render_template('sponsor_login.html', error="Your account has been flagged. Please contact admin.")
                else:
                    if this_sponsor.user_role != 1:
                        return render_template('sponsor_login.html', error="You are not registered as a sponsor")
                    else:
                        this_sponsor = sponsor
                        login_user(this_sponsor)


        #add features of dashboard

        return render_template('sponsor_dashboard.html', current_user=this_sponsor, u_name=u_name)
    return render_template('sponsor_login.html')
