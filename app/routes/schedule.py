import calendar
from datetime import date, timedelta, datetime

from flask import Blueprint, render_template, request
from flask_login import login_required

from ..extensions import db
from ..models.work_info import WorkInfo
from ..models.ctm_people import CTMPeople

bp = Blueprint("schedule", __name__, url_prefix="/schedule")


@bp.get("")
@login_required
def index():
    today = date.today()
    year = int(request.args.get("y", today.year))
    month = int(request.args.get("m", today.month))

    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    weeks = cal.monthdatescalendar(year, month)

    start = weeks[0][0]
    end = weeks[-1][-1]

    # Work_Date는 DateTime이라 날짜 범위로 조회
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    rows = (
        db.session.query(WorkInfo, CTMPeople)
        .join(CTMPeople, CTMPeople.Person_ID == WorkInfo.Person_ID)
        .filter(WorkInfo.Work_Date >= start_dt)
        .filter(WorkInfo.Work_Date <= end_dt)
        .order_by(WorkInfo.Work_Date.asc(), WorkInfo.Work_ID.asc())
        .all()
    )

    by_day: dict[date, list[tuple[WorkInfo, CTMPeople]]] = {}
    for work, people in rows:
        if work.Work_Date is None:
            continue
        # Work_Date가 이미 date 객체인 경우 처리
        work_date = work.Work_Date if isinstance(work.Work_Date, date) else work.Work_Date.date()
        by_day.setdefault(work_date, []).append((work, people))

    first = date(year, month, 1)
    prev_month_last_day = first - timedelta(days=1)
    next_month_first_day = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    return render_template(
        "schedule/index.html",
        year=year,
        month=month,
        weeks=weeks,
        by_day=by_day,
        prev_y=prev_month_last_day.year,
        prev_m=prev_month_last_day.month,
        next_y=next_month_first_day.year,
        next_m=next_month_first_day.month,
    )