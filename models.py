from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class WebUsers(UserMixin, db.Model):
    __tablename__ = 'web_users'
    __mapper_args__ = {'eager_defaults': True}
    __table_args__ = {'implicit_returning': False}

    id                  = db.Column('ID',                   db.Numeric(19),  primary_key=True, nullable=False, autoincrement=False)
    email               = db.Column('EMAIL',                db.String(255),  nullable=False, unique=True)
    password_hash       = db.Column('PASSWORD_HASH',        db.String(255),  nullable=False)
    is_active           = db.Column('IS_ACTIVE',            db.Numeric(1),   nullable=False, default=1)
    is_admin            = db.Column('IS_ADMIN',             db.String(1),    nullable=True,  default='N')
    agent_name          = db.Column('AGENT_NAME',           db.String(255),  nullable=True)
    address             = db.Column('ADDRESS',              db.String(500),  nullable=True)
    created_at          = db.Column('CREATED_AT',           db.Date,         nullable=False)
    updated_at          = db.Column('UPDATED_AT',           db.Date,         nullable=False)
    password_changed_at = db.Column('PASSWORD_CHANGED_AT',  db.Date,         nullable=False)

    def get_id(self):
        return str(self.id)

    @property
    def is_active_user(self):
        return int(self.is_active) == 1

    @property
    def is_admin_user(self):
        return self.is_admin == 'Y'

    def __repr__(self):
        return f'<WebUsers id={self.id} email={self.email}>'


class WebIgm(db.Model):
    """WEB_IGM - igm_id auto from igm_web_seq via BEFORE INSERT trigger"""
    __tablename__ = 'WEB_IGM'
    __mapper_args__ = {'eager_defaults': True}

    igm_id          = db.Column('IGM_ID',           db.Numeric,         primary_key=True, nullable=False, autoincrement=False)
    m_bl_no         = db.Column('M_BL_NO',          db.String(30),      nullable=True)
    bl_no           = db.Column('BL_NO',            db.String(30),      nullable=True)
    bl_date         = db.Column('BL_DATE',          db.Date,            nullable=True)
    pol             = db.Column('POL',              db.String(5),       nullable=True)
    pod             = db.Column('POD',              db.String(5),       nullable=True)
    fright_con      = db.Column('FRIGHT_CON',       db.Numeric(12, 2),  nullable=True)
    frieght_type    = db.Column('FRIEGHT_TYPE',     db.String(1),       nullable=True)
    manifest_type   = db.Column('MANIFEST_TYPE',    db.String(15),      nullable=True)
    shp_name        = db.Column('SHP_NAME',         db.String(60),      nullable=True)
    shp_adr1        = db.Column('SHP_ADR1',         db.String(60),      nullable=True)
    shp_adr2        = db.Column('SHP_ADR2',         db.String(60),      nullable=True)
    shp_adr3        = db.Column('SHP_ADR3',         db.String(60),      nullable=True)
    shp_country     = db.Column('SHP_COUNTRY',      db.String(5),       nullable=True)
    cne_name        = db.Column('CNE_NAME',         db.String(60),      nullable=True)
    cne_adr1        = db.Column('CNE_ADR1',         db.String(60),      nullable=True)
    cne_adr2        = db.Column('CNE_ADR2',         db.String(60),      nullable=True)
    cne_adr3        = db.Column('CNE_ADR3',         db.String(60),      nullable=True)
    cne_ntn         = db.Column('CNE_NTN',          db.String(20),      nullable=True)
    ntfy_name       = db.Column('NTFY_NAME',        db.String(60),      nullable=True)
    ntfy_adr1       = db.Column('NTFY_ADR1',        db.String(60),      nullable=True)
    ntfy_adr2       = db.Column('NTFY_ADR2',        db.String(60),      nullable=True)
    ntfy_adr3       = db.Column('NTFY_ADR3',        db.String(60),      nullable=True)
    commodity       = db.Column('COMMODITY',        db.String(20),      nullable=True)
    hs_code         = db.Column('HS_CODE',          db.String(20),      nullable=True)
    dsc_of_goods    = db.Column('DSC_OF_GOODS',     db.String(500),     nullable=True)
    marks           = db.Column('MARKS',            db.String(200),     nullable=True)
    created_by      = db.Column('CREATED_BY',       db.String(255),     nullable=True)
    is_locked       = db.Column('IS_LOCKED',        db.String(1),       nullable=True, default='N')

    containers      = db.relationship('WebIgmCnt', backref='igm', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<WebIgm igm_id={self.igm_id} bl_no={self.bl_no}>'


class WebIgmCnt(db.Model):
    """WEB_IGM_CNT - composite PK: igm_id + sr_no"""
    __tablename__ = 'WEB_IGM_CNT'

    igm_id          = db.Column('IGM_ID',       db.Numeric,      db.ForeignKey('WEB_IGM.IGM_ID'), primary_key=True, nullable=False)
    sr_no           = db.Column('SR_NO',         db.Numeric,      primary_key=True, nullable=False)
    cnt_no          = db.Column('CNT_NO',        db.String(11),   nullable=True)
    seal_no         = db.Column('SEAL_NO',       db.String(30),   nullable=True)
    size            = db.Column('CNT_SIZE',      db.String(2),    nullable=True)
    type            = db.Column('CNT_TYPE',      db.String(2),    nullable=True)
    term            = db.Column('TERM',          db.String(7),    nullable=True)
    packages        = db.Column('PACKAGES',      db.String(10),   nullable=True)
    no_of_pkgs      = db.Column('NO_OF_PKGS',    db.Numeric(8),   nullable=True)
    net_weight      = db.Column('NET_WEIGHT',    db.Numeric(8,2), nullable=True)
    gross_weight    = db.Column('GROSS_WEIGHT',  db.Numeric(8,2), nullable=True)

    def __repr__(self):
        return f'<WebIgmCnt igm_id={self.igm_id} sr_no={self.sr_no}>'


class Packages(db.Model):
    """PACKAGES lookup table"""
    __tablename__ = 'PACKAGES'

    pkg_id      = db.Column('PKG_ID',      db.String(8),   primary_key=True, nullable=False)
    pkg_code    = db.Column('PKG_CODE',    db.String(8),   nullable=False)
    name        = db.Column('NAME',        db.String(50),  nullable=False)
    lin_id      = db.Column('LIN_ID',      db.String(4),   nullable=False)
    edi_code    = db.Column('EDI_CODE',    db.String(20),  nullable=True)

    def __repr__(self):
        return f'<Packages pkg_id={self.pkg_id} name={self.name}>'


class Commodity(db.Model):
    """COMMODITY lookup table"""
    __tablename__ = 'COMMODITY'

    cmd_id      = db.Column('CMD_ID',      db.String(8),   primary_key=True, nullable=False)
    cmd_code    = db.Column('CMD_CODE',    db.String(8),   nullable=False)
    name        = db.Column('NAME',        db.String(50),  nullable=True)
    edi_code    = db.Column('EDI_CODE',    db.String(20),  nullable=True)
    un_code     = db.Column('UN_CODE',     db.String(10),  nullable=True)
    imco_no     = db.Column('IMCO_NO',     db.String(10),  nullable=True)
    lin_id      = db.Column('LIN_ID',      db.String(4),   nullable=True)
    is_dg       = db.Column('IS_DG',       db.String(1),   nullable=True)
    page_no     = db.Column('PAGE_NO',     db.String(10),  nullable=True)
    pctcode     = db.Column('PCTCODE',     db.String(10),  nullable=True)
    cmd_type    = db.Column('CMD_TYPE',    db.String(20),  nullable=True)
    is_stop     = db.Column('IS_STOP',     db.String(1),   nullable=True)
    is_print    = db.Column('IS_PRINT',    db.String(1),   nullable=True)

    def __repr__(self):
        return f'<Commodity cmd_id={self.cmd_id} name={self.name}>'


class Ports(db.Model):
    """PORTS lookup table"""
    __tablename__ = 'PORT'

    prt_id      = db.Column('PRT_ID',      db.String(8),   primary_key=True, nullable=False)
    prt_code    = db.Column('PRT_CODE',    db.String(6),   nullable=False)
    name        = db.Column('NAME',        db.String(30),  nullable=True)
    cnt_id      = db.Column('CNT_ID',      db.String(4),   nullable=True)
    lin_id      = db.Column('LIN_ID',      db.String(4),   nullable=True)

    def __repr__(self):
        return f'<Ports prt_id={self.prt_id} prt_code={self.prt_code}>'