    // [1] 작업 상세 (달력 클릭)
    function openDashboardDetail(workId, companyName) {
        const modal = new bootstrap.Modal(document.getElementById('dashboardDetailModal'));
        const body = document.getElementById('dashboardDetailBody');
        body.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
        modal.show();

        Promise.all([
            fetch(`/work/ajax/${workId}/detail`).then(r => r.json()),
            fetch(`/work/ajax/${workId}/attachments`).then(r => r.json())
        ])
        .then(([detailRes, attRes]) => {
            if (!detailRes.ok) throw new Error(detailRes.message);
            const d = detailRes.data;
            const items = attRes.items || [];
            let fileHtml = '<span class="text-muted small">첨부파일 없음</span>';
            if (items.length > 0) {
                fileHtml = `<ul class="list-group list-group-flush border rounded">` +
                    items.map(f => `
                        <li class="list-group-item d-flex justify-content-between align-items-center p-2">
                            <a href="${f.url}" class="text-decoration-none text-dark text-truncate">
                                <i class="bi bi-file-earmark me-2 text-secondary"></i>${f.name}
                            </a>
                            <span class="badge bg-secondary rounded-pill">${f.size}</span>
                        </li>`).join('') + `</ul>`;
            }
            body.innerHTML = `
                <div class="row g-4">
                    <div class="col-md-6 border-end">
                        <div class="mb-3"><label class="small text-muted fw-bold">고객사</label><div class="fs-5 fw-bold text-dark">${companyName}</div></div>
                        <div class="mb-3"><label class="small text-muted fw-bold">작업일</label><div>${d.work_date}</div></div>
                        <div class="mb-3"><label class="small text-muted fw-bold">유형</label><div><span class="badge bg-primary bg-opacity-10 text-primary">${d.work_type}</span></div></div>
                        <div class="mb-0"><label class="small text-muted fw-bold">등록자</label><div>${d.submitter || '-'}</div></div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3"><label class="small text-muted fw-bold">요약</label><div class="fw-bold">${d.summary || '-'}</div></div>
                        <div class="mb-3"><label class="small text-muted fw-bold">상세 내용</label><div class="p-3 bg-light rounded border" style="white-space: pre-wrap; font-size: 0.9rem;">${d.description || '-'}</div></div>
                        <div><label class="small text-muted fw-bold mb-2">첨부파일</label><div>${fileHtml}</div></div>
                    </div>
                </div>`;
        }).catch(err => {
            console.error(err);
            body.innerHTML = '<div class="text-center py-5 text-danger">정보를 불러오지 못했습니다.</div>';
        });
    }

    // [2] SR 상세 (우측 리스트 클릭)
    function openDashboardSrDetail(srId) {
        const modal = new bootstrap.Modal(document.getElementById('dashboardSrDetailModal'));
        const body = document.getElementById('dashboardSrDetailBody');
        body.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-warning"></div></div>';
        modal.show();

        fetch(`/sr/ajax/${srId}`)
        .then(r => r.json())
        .then(json => {
            if (!json.ok) throw new Error(json.message);
            const d = json.data;

            const severityBadge = d.severity === 'High' ? '<span class="badge bg-danger">High</span>' :
                                  d.severity === 'Middle' ? '<span class="badge bg-warning text-dark">Middle</span>' :
                                  '<span class="badge bg-secondary">Low</span>';
            const resultBadge = d.result === '완료' ? '<span class="badge bg-success">완료</span>' : '<span class="badge bg-secondary">미완료</span>';

            body.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6 border-end">
                        <div class="mb-3">
                            <label class="small text-muted fw-bold">고객사 (사이트)</label>
                            <div class="fs-5 fw-bold text-dark">${d.company}</div>
                            <div class="small text-muted">${d.location}</div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6"><label class="small text-muted fw-bold">중요도</label><div>${severityBadge}</div></div>
                            <div class="col-6"><label class="small text-muted fw-bold">상태</label><div>${resultBadge}</div></div>
                        </div>
                        <div class="mb-0">
                            <label class="small text-muted fw-bold">요청자 / 요청일</label>
                            <div>${d.requester || '-'} <span class="text-muted mx-1">|</span> ${d.request_date}</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="small text-muted fw-bold">요청 내용</label>
                            <div class="p-3 bg-light rounded border text-break" style="min-height: 100px; white-space: pre-wrap;">${d.content}</div>
                        </div>
                        <div class="mb-0">
                            <label class="small text-muted fw-bold">처리 정보</label>
                            <div class="small text-muted">
                                처리자: <span class="text-dark fw-bold">${d.handler || '-'}</span><br>
                                처리일: <span class="text-dark">${d.handled_date || '-'}</span>
                            </div>
                        </div>
                    </div>
                </div>`;
        })
        .catch(err => {
            console.error(err);
            body.innerHTML = '<div class="text-center py-5 text-danger">정보를 불러오지 못했습니다.</div>';
        });
    }