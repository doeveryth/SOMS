from datetime import datetime, timedelta, date
import calendar
from flask import Blueprint, render_template
from flask_login import login_required

from ..extensions import db
from ..models.customer_notes import CustomerNote
from ..models.work_info import WorkInfo
from ..models.sr_ticket import SRTicket

bp = Blueprint("dashboard", __name__, url_prefix="/")


@bp.get("/")
@login_required
def index():
    now = datetime.utcnow()
    since = now - timedelta(days=7)

    recent_notes = (
        db.session.query(CustomerNote)
        .filter(CustomerNote.Created_At >= since)
        .order_by(CustomerNote.Created_At.desc())
        .limit(10)
        .all()
    )

    recent_work = (
        db.session.query(WorkInfo)
        .filter(WorkInfo.Create_Date >= since)
        .order_by(WorkInfo.Create_Date.desc())
        .limit(10)
        .all()
    )

    today = date.today()
    year, month = today.year, today.month
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)
    start = weeks[0][0]
    end = weeks[-1][-1]

    sr_items = (
        db.session.query(SRTicket)
        .filter(SRTicket.request_date >= start)
        .filter(SRTicket.request_date <= end)
        .order_by(SRTicket.request_date.asc(), SRTicket.sr_id.asc())
        .all()
    )
    sr_by_day: dict[date, list[SRTicket]] = {}
    for it in sr_items:
        sr_by_day.setdefault(it.request_date, []).append(it)

    return render_template(
        "dashboard/index.html",
        recent_notes=recent_notes,
        recent_work=recent_work,
        cal_year=year,
        cal_month=month,
        cal_weeks=weeks,
        sr_by_day=sr_by_day,
    )