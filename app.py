from flask import Flask, render_template, redirect, url_for, flash, request, session, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from config import Config
from models import db, WebUsers, WebIgm, WebIgmCnt, Packages, Commodity, Ports
from pdf_bl import generate_bl_pdf

# ---------------------------------------------------
# App Initialization
# ---------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------
# Database
# ---------------------------------------------------
db.init_app(app)

# ---------------------------------------------------
# Flask-Login Setup
# ---------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return WebUsers.query.get(int(user_id))

# ---------------------------------------------------
# Dashboard
# ---------------------------------------------------
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# ---------------------------------------------------
# Login / Logout
# ---------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = WebUsers.query.filter_by(email=email).first()

        if not user:
            flash('No account found with that email.', 'danger')
        elif not int(user.is_active):
            flash('Your account is inactive. Contact administrator.', 'danger')
        elif user.password_hash != password:
            flash('Incorrect password. Please try again.', 'danger')
        else:
            login_user(user, remember=False)
            flash(f'Welcome, {user.email}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ---------------------------------------------------
# Users
# ---------------------------------------------------
@app.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin_user:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        is_active        = request.form.get('is_active', '1')
        is_admin         = request.form.get('is_admin', 'N')
        agent_name       = request.form.get('agent_name', '').strip()
        address          = request.form.get('address', '').strip()

        error = None
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif WebUsers.query.filter_by(email=email).first():
            error = f'Email "{email}" is already registered.'

        if error:
            flash(error, 'danger')
            return render_template('create_user.html', form_data=request.form)

        now = datetime.utcnow()
        # Get next ID from sequence manually
        result = db.session.execute(db.text('SELECT user_seq.NEXTVAL FROM DUAL'))
        next_id = result.scalar()
        new_user = WebUsers(
            id                  = next_id,
            email               = email,
            password_hash       = password,
            is_active           = int(is_active),
            is_admin            = is_admin,
            agent_name          = agent_name or None,
            address             = address or None,
            created_at          = now,
            updated_at          = now,
            password_changed_at = now
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'User "{email}" created successfully!', 'success')
            return redirect(url_for('user_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
            return render_template('create_user.html', form_data=request.form)

    return render_template('create_user.html', form_data=None)


@app.route('/users')
@login_required
def user_list():
    if not current_user.is_admin_user:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('dashboard'))
    users = WebUsers.query.order_by(WebUsers.created_at.desc()).all()
    return render_template('user_list.html', users=users)

# ---------------------------------------------------
# IGM Routes
# ---------------------------------------------------
@app.route('/igm')
@login_required
def igm_list():
    if current_user.is_admin_user:
        igms = WebIgm.query.order_by(WebIgm.igm_id.desc()).all()
    else:
        igms = WebIgm.query.filter_by(created_by=current_user.email).order_by(WebIgm.igm_id.desc()).all()
    return render_template('igm_list.html', igms=igms)


@app.route('/igm/new', methods=['GET', 'POST'])
@login_required
def igm_new():
    if request.method == 'POST':
        try:
            # Get next IGM_ID from sequence manually
            result = db.session.execute(db.text('SELECT igm_web_seq.NEXTVAL FROM DUAL'))
            next_id = result.scalar()

            igm = WebIgm(
                igm_id        = next_id,
                m_bl_no       = request.form.get('m_bl_no', '').strip() or None,
                bl_no         = request.form.get('bl_no', '').strip() or None,
                bl_date       = datetime.strptime(request.form.get('bl_date'), '%Y-%m-%d').date() if request.form.get('bl_date') else None,
                pol           = request.form.get('pol', '').strip()[:5] or None,
                pod           = request.form.get('pod', '').strip()[:5] or None,
                fright_con    = float(request.form.get('fright_con')) if request.form.get('fright_con') else None,
                frieght_type  = request.form.get('frieght_type') or None,
                manifest_type = request.form.get('manifest_type') or None,
                shp_name      = request.form.get('shp_name', '').strip() or None,
                shp_adr1      = request.form.get('shp_adr1', '').strip() or None,
                shp_adr2      = request.form.get('shp_adr2', '').strip() or None,
                shp_adr3      = request.form.get('shp_adr3', '').strip() or None,
                shp_country   = request.form.get('shp_country', '').strip().upper() or None,
                cne_name      = request.form.get('cne_name', '').strip() or None,
                cne_adr1      = request.form.get('cne_adr1', '').strip() or None,
                cne_adr2      = request.form.get('cne_adr2', '').strip() or None,
                cne_adr3      = request.form.get('cne_adr3', '').strip() or None,
                cne_ntn       = request.form.get('cne_ntn', '').strip() or None,
                ntfy_name     = request.form.get('ntfy_name', '').strip() or None,
                ntfy_adr1     = request.form.get('ntfy_adr1', '').strip() or None,
                ntfy_adr2     = request.form.get('ntfy_adr2', '').strip() or None,
                ntfy_adr3     = request.form.get('ntfy_adr3', '').strip() or None,
                commodity     = request.form.get('commodity', '').strip() or None,
                hs_code       = request.form.get('hs_code', '').strip() or None,
                dsc_of_goods  = request.form.get('dsc_of_goods', '').strip() or None,
                marks         = request.form.get('marks', '').strip() or None,
                created_by    = current_user.email,
            )
            db.session.add(igm)
            # Use next_id directly — no flush needed

            cnt_nos       = request.form.getlist('cnt_no')
            seal_nos      = request.form.getlist('seal_no')
            sizes         = request.form.getlist('cnt_size')
            types         = request.form.getlist('cnt_type')
            terms         = request.form.getlist('term')
            packages      = request.form.getlist('packages')
            no_of_pkgs    = request.form.getlist('no_of_pkgs')
            net_weights   = request.form.getlist('net_weight')
            gross_weights = request.form.getlist('gross_weight')

            for i, cnt_no in enumerate(cnt_nos):
                if not cnt_no.strip():
                    continue
                cnt = WebIgmCnt(
                    igm_id       = next_id,
                    sr_no        = i + 1,
                    cnt_no       = cnt_no.strip() or None,
                    seal_no      = seal_nos[i].strip() if i < len(seal_nos) else None,
                    size         = sizes[i].strip() if i < len(sizes) else None,
                    type         = types[i].strip() if i < len(types) else None,
                    term         = terms[i].strip() if i < len(terms) else None,
                    packages     = packages[i].strip() if i < len(packages) else None,
                    no_of_pkgs   = int(no_of_pkgs[i]) if i < len(no_of_pkgs) and no_of_pkgs[i] else None,
                    net_weight   = float(net_weights[i]) if i < len(net_weights) and net_weights[i] else None,
                    gross_weight = float(gross_weights[i]) if i < len(gross_weights) and gross_weights[i] else None,
                )
                db.session.add(cnt)

            db.session.commit()
            flash(f'IGM saved successfully! IGM ID: {igm.igm_id}', 'success')
            return redirect(url_for('igm_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error saving IGM: {str(e)}', 'danger')
            packages    = Packages.query.order_by(Packages.name).all()
            commodities = Commodity.query.order_by(Commodity.name).all()
            ports       = Ports.query.filter_by(lin_id='0002').order_by(Ports.prt_code).all()
            return render_template('igm_form.html', form_data=request.form, packages=packages, commodities=commodities, ports=ports)

    packages    = Packages.query.order_by(Packages.name).all()
    commodities = Commodity.query.order_by(Commodity.name).all()
    ports       = Ports.query.filter_by(lin_id='0002').order_by(Ports.prt_code).all()
    return render_template('igm_form.html', form_data=None, packages=packages, commodities=commodities, ports=ports)

@app.route('/igm/<int:igm_id>/edit', methods=['GET', 'POST'])
@login_required
def igm_edit(igm_id):
    igm = WebIgm.query.get_or_404(igm_id)

    # Access control
    if not current_user.is_admin_user and igm.created_by != current_user.email:
        flash('Access denied. You can only edit your own records.', 'danger')
        return redirect(url_for('igm_list'))

    # Lock check — only admin can edit locked records
    if igm.is_locked == 'Y' and not current_user.is_admin_user:
        flash('This record is locked by admin and cannot be edited.', 'warning')
        return redirect(url_for('igm_list'))

    if request.method == 'POST':
        try:
            # Update IGM header
            igm.m_bl_no       = request.form.get('m_bl_no', '').strip() or None
            igm.bl_no         = request.form.get('bl_no', '').strip() or None
            igm.bl_date       = datetime.strptime(request.form.get('bl_date'), '%Y-%m-%d').date() if request.form.get('bl_date') else None
            igm.pol           = request.form.get('pol', '').strip()[:5] or None
            igm.pod           = request.form.get('pod', '').strip()[:5] or None
            igm.fright_con    = float(request.form.get('fright_con')) if request.form.get('fright_con') else None
            igm.frieght_type  = request.form.get('frieght_type') or None
            igm.manifest_type = request.form.get('manifest_type') or None
            igm.shp_name      = request.form.get('shp_name', '').strip() or None
            igm.shp_adr1      = request.form.get('shp_adr1', '').strip() or None
            igm.shp_adr2      = request.form.get('shp_adr2', '').strip() or None
            igm.shp_adr3      = request.form.get('shp_adr3', '').strip() or None
            igm.shp_country   = request.form.get('shp_country', '').strip().upper() or None
            igm.cne_name      = request.form.get('cne_name', '').strip() or None
            igm.cne_adr1      = request.form.get('cne_adr1', '').strip() or None
            igm.cne_adr2      = request.form.get('cne_adr2', '').strip() or None
            igm.cne_adr3      = request.form.get('cne_adr3', '').strip() or None
            igm.cne_ntn       = request.form.get('cne_ntn', '').strip() or None
            igm.ntfy_name     = request.form.get('ntfy_name', '').strip() or None
            igm.ntfy_adr1     = request.form.get('ntfy_adr1', '').strip() or None
            igm.ntfy_adr2     = request.form.get('ntfy_adr2', '').strip() or None
            igm.ntfy_adr3     = request.form.get('ntfy_adr3', '').strip() or None
            igm.commodity     = request.form.get('commodity', '').strip() or None
            igm.hs_code       = request.form.get('hs_code', '').strip() or None
            igm.dsc_of_goods  = request.form.get('dsc_of_goods', '').strip() or None
            igm.marks         = request.form.get('marks', '').strip() or None

            # Delete old containers and re-insert
            WebIgmCnt.query.filter_by(igm_id=igm.igm_id).delete()

            cnt_nos       = request.form.getlist('cnt_no')
            seal_nos      = request.form.getlist('seal_no')
            sizes         = request.form.getlist('cnt_size')
            types         = request.form.getlist('cnt_type')
            terms         = request.form.getlist('term')
            packages      = request.form.getlist('packages')
            no_of_pkgs    = request.form.getlist('no_of_pkgs')
            net_weights   = request.form.getlist('net_weight')
            gross_weights = request.form.getlist('gross_weight')

            for i, cnt_no in enumerate(cnt_nos):
                if not cnt_no.strip():
                    continue
                cnt = WebIgmCnt(
                    igm_id       = igm.igm_id,
                    sr_no        = i + 1,
                    cnt_no       = cnt_no.strip() or None,
                    seal_no      = seal_nos[i].strip() if i < len(seal_nos) else None,
                    size         = sizes[i].strip() if i < len(sizes) else None,
                    type         = types[i].strip() if i < len(types) else None,
                    term         = terms[i].strip() if i < len(terms) else None,
                    packages     = packages[i].strip() if i < len(packages) else None,
                    no_of_pkgs   = int(no_of_pkgs[i]) if i < len(no_of_pkgs) and no_of_pkgs[i] else None,
                    net_weight   = float(net_weights[i]) if i < len(net_weights) and net_weights[i] else None,
                    gross_weight = float(gross_weights[i]) if i < len(gross_weights) and gross_weights[i] else None,
                )
                db.session.add(cnt)

            db.session.commit()
            flash(f'IGM {igm.igm_id} updated successfully!', 'success')
            return redirect(url_for('igm_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating IGM: {str(e)}', 'danger')
            packages    = Packages.query.order_by(Packages.name).all()
            commodities = Commodity.query.filter_by(lin_id='0001').order_by(Commodity.name).all()
            ports       = Ports.query.filter_by(lin_id='0001').order_by(Ports.prt_code).all()
            return render_template('igm_form.html', igm=igm, form_data=request.form,
                                   packages=packages, commodities=commodities, ports=ports, edit=True)

    packages    = Packages.query.order_by(Packages.name).all()
    commodities = Commodity.query.filter_by(lin_id='0001').order_by(Commodity.name).all()
    ports       = Ports.query.filter_by(lin_id='0001').order_by(Ports.prt_code).all()
    return render_template('igm_form.html', igm=igm, form_data=None,
                           packages=packages, commodities=commodities, ports=ports, edit=True)


@app.route('/igm/<int:igm_id>/lock', methods=['POST'])
@login_required
def igm_lock(igm_id):
    if not current_user.is_admin_user:
        flash('Only admin can lock/unlock records.', 'danger')
        return redirect(url_for('igm_list'))
    igm = WebIgm.query.get_or_404(igm_id)
    igm.is_locked = 'N' if igm.is_locked == 'Y' else 'Y'
    db.session.commit()
    status = 'locked' if igm.is_locked == 'Y' else 'unlocked'
    flash(f'IGM {igm.igm_id} {status} successfully!', 'success')
    return redirect(url_for('igm_list'))


@app.route('/igm/<int:igm_id>/pdf')
@login_required
def igm_pdf(igm_id):
    igm = WebIgm.query.get_or_404(igm_id)
    # Non-admin can only print their own
    if not current_user.is_admin_user and igm.created_by != current_user.email:
        flash('Access denied.', 'danger')
        return redirect(url_for('igm_list'))
    if igm.commodity:
        from models import Commodity
        cmd = Commodity.query.filter_by(cmd_id=igm.commodity).first()
        if cmd:
            commodity_name = cmd.name.strip() if cmd.name else igm.commodity
        else:
            commodity_name = igm.commodity
    else:
        commodity_name = None
    pdf_bytes = generate_bl_pdf(
        igm,
        commodity_name=commodity_name,
        forwarder_name=current_user.agent_name,
        forwarder_address=current_user.address
    )
    filename  = f'BL_{igm.bl_no or igm.igm_id}.pdf'
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename={filename}'}
    )

# ---------------------------------------------------
# Run
# ---------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)