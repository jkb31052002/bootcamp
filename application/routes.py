from flask import Flask, render_template, request, url_for, session, flash, abort, redirect
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from flask import current_app as app
from datetime import datetime, date
from .models import *


#ACTIVE CAMPAIGNS
def campaign_isactive(start_date, end_date, present_date):
    present_date = date.today()
    return start_date <= present_date < end_date


#PROGRESS CALCULATION
def calculate_campaign_progress(start_date, end_date):
    current_date = date.today()
    total_days = (end_date - start_date).days
    elapsed_days = (current_date - start_date).days
    if total_days > 0:
        progress = (elapsed_days / total_days) * 100
    else:
        progress = 0
    return round(progress, 2)


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

                        adrequests = db.session.query(Adrequests).join(Campaign).join(Influencer).filter(
                            Campaign.sponsor_id == sponsor.sponsor_id,
                            Campaign.flagged == 0,
                            Influencer.flagged == 0,
                            Adrequests.status.in_(["Requested to Sponsor", "Accepted by Sponsor"])
                        ).all()

                        campaigns = Campaign.query.filter_by(sponsor_id = sponsor.sponsor_id, flagged = 0).all()

                        active_campaigns = []

                        for campaign in campaigns:
                            if(campaign_isactive(campaign.start_date, campaign.end_date, date.today())):
                                active_campaigns.append(campaign)


        #add features of dashboard

        return render_template('sponsor_dashboard.html', current_user=this_sponsor, u_name=u_name, adrequests=adrequests, campaigns=active_campaigns, id=User.id, calculate_campaign_progress=calculate_campaign_progress)
    return render_template('sponsor_login.html')


#SPONSOR LOGOUT
@app.route('/sponsor_logout')
@login_required
def sponsor_logout():
    logout_user()
    return render_template('sponsor_login.html')


#SPONSOR DASHBOARD
@app.route('/sponsor_dash', methods=['GET', 'POST'])
@login_required
def sponsor_dash():
    user_id = current_user.id
    user = User.query.filter_by(id=user_id).first()
    sponsor = Sponsor.query.filter_by(sponsor_id=user.id).first()

    adrequests = db.session.query(Adrequests).join(Campaign).join(Influencer).filter(
        Campaign.sponsor_id == current_user.id,
        Campaign.flagged == 0,
        Influencer.flagged == 0,
        Adrequests.status.in_(["Requested to Sponsor", "Accepted by Sponsor"])
    ).all()

    campaigns = Campaign.query.filter_by(sponsor_id = current_user.id, flagged = 0).all()

    active_campaigns = []

    for campaign in campaigns:
        if(campaign_isactive(campaign.start_date, campaign.end_date, date.today())):
            active_campaigns.append(campaign)
    
    return render_template('sponsor_dashboard.html', adrequests=adrequests, u_name=current_user.username, id=User.id, campaigns=active_campaigns, calculate_campaign_progress=calculate_campaign_progress)

#SPONSOR CREATE CAMPAIGN
@app.route('/create_campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        name = request.form.get("name")
        desc = request.form.get("desc")
        budget = int(request.form.get("budget"))
        if budget <=0:
            return render_template('create_campaign.html', message="Budget must be greater than 0")
        niche = request.form.get("niche")
        sdate = request.form.get("sdate")
        sdate = datetime.strptime(sdate, '%Y-%m-%d').date()
        edate = request.form.get("edate")
        edate = datetime.strptime(edate, '%Y-%m-%d').date()
        current_date = date.today()
        if edate < sdate:
            return render_template('create_campaign.html', message="End date must be after start date")
        if edate < current_date:
            return render_template('create_campaign.html', message="End date must be in the future")
        visibility = request.form.get("visibility").lower()
        goals = request.form.get("goals")
        this_id = current_user.id
        sponsor = Sponsor.query.filter_by(sponsor_id=this_id).first()
        new_campaign = Campaign(name=name, description=desc, campaign_budget=budget, start_date=sdate, end_date=edate, visibility=visibility, goals=goals, niche=niche, sponsor_id=current_user.id)
        db.session.add(new_campaign)
        db.session.commit()
        return redirect('/sponsor_campaign')
    return render_template('create_campaign.html')


#SPONSOR EDIT CAMPAIGN
@app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if request.method == 'POST':
        name = request.form.get("name")
        desc = request.form.get("desc")
        budget = int(request.form.get("budget"))
        if budget <=0:
            return render_template('create_campaign.html', message="Budget must be greater than 0")
        niche = request.form.get("niche")
        sdate = request.form.get("sdate")
        sdate = datetime.strptime(sdate, '%Y-%m-%d').date()
        edate = request.form.get("edate")
        edate = datetime.strptime(edate, '%Y-%m-%d').date()
        current_date = date.today()
        if edate < sdate:
            return render_template('create_campaign.html', message="End date must be after start date")
        if edate < current_date:
            return render_template('create_campaign.html', message="End date must be in the future")
        visibility = request.form.get("visibility").lower()
        goals = request.form.get("goals")


        campaign.name = name
        campaign.description = desc
        campaign.campaign_budget = budget
        campaign.start_date = sdate
        campaign.end_date = edate
        campaign.visibility = visibility
        campaign.goals = goals
        campaign.niche = niche

        db.session.commit()
        return redirect('/sponsor_campaign')
    return render_template('edit_campaign.html', campaign=campaign)


#SPONSOR DELETE CAMPAIGN
@app.route('/delete_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if campaign:
        db.session.delete(campaign)
        db.session.commit()
    return redirect(url_for('sponsor_campaign'))


#SPONSOR VIEW CAMPAIGNS
@app.route('/view_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def view_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    adrequests = db.session.query(Adrequests).join(Influencer).filter(
        Adrequests.campaign_id == campaign.id,
        Adrequests.sent_by_sponsor == True,
        Influencer.flagged == 0,
    ).all()
    progress = calculate_campaign_progress(campaign.start_date, campaign.end_date)
    return render_template('view_campaign.html', campaign=campaign, adrequests=adrequests, progress=progress)

#SPONSOR CAMPAIGNS PAGE
@app.route('/sponsor_campaign', methods=['GET', 'POST'])
@login_required
def sponsor_campaign():
    this_id = current_user.id
    sponsor = Sponsor.query.filter_by(sponsor_id=this_id).first()

    campaigns = Campaign.query.filter_by(sponsor_id=current_user.id, flagged=0).all()
    return render_template('sponsor_campaign.html', campaigns=campaigns, sponsor=sponsor, calculate_campaign_progress=calculate_campaign_progress)