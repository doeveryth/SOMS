from flask import Blueprint, render_template
from datetime import date
import calendar
from sqlalchemy import desc

from ..extensions import db
from ..models.work_info import WorkInfo
from ..models.ctm_people import CTMPeople
from ..models.sr_ticket import SRTicket  # [추가] SR 모델 임포트

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
def index():
    today = date.today()
    year = today.year
    month = today.month

    # ---------------------------------------------------------
    # [1] 달력 데이터 (작업 일정)
    # ---------------------------------------------------------
    cal = calendar.Calendar(firstweekday=6)
    cal_weeks = cal.monthdatescalendar(year, month)

    start_date = cal_weeks[0][0]
    end_date = cal_weeks[-1][-1]

    calendar_works = (
        db.session.query(WorkInfo, CTMPeople)
        .join(CTMPeople, WorkInfo.Person_ID == CTMPeople.Person_ID)
        .filter(WorkInfo.Work_Date >= start_date)
        .filter(WorkInfo.Work_Date <= end_date)
        .order_by(WorkInfo.Work_Date.asc())
        .all()
    )

    sr_by_day = {}
    for w, p in calendar_works:
        if w.Work_Date not in sr_by_day:
            sr_by_day[w.Work_Date] = []

        sr_by_day[w.Work_Date].append({
            'id': w.Work_ID,
            'company': p.Company,
            'location': p.Last_Name,
            'type': w.Work_Type
        })

    # ---------------------------------------------------------
    # [2] 최근 SR (Service Request) - 5건 [변경됨]
    # ---------------------------------------------------------
    recent_sr = (
        db.session.query(SRTicket)
        .order_by(SRTicket.request_date.desc(), SRTicket.sr_id.desc())
        .limit(5)
        .all()
    )

    # ---------------------------------------------------------
    # [3] 계약 만료 임박
    # ---------------------------------------------------------
    expiring_contracts = (
        db.session.query(CTMPeople)
        .filter(CTMPeople.Terminate_Date != None)
        .filter(CTMPeople.Terminate_Date >= today)
        .order_by(CTMPeople.Terminate_Date.asc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashboard/index.html',
        cal_year=year,
        cal_month=month,
        cal_weeks=cal_weeks,
        sr_by_day=sr_by_day,
        recent_sr=recent_sr,  # [변경] recent_work -> recent_sr 전달
        expiring_contracts=expiring_contracts
    )