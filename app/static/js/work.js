/**
 * work.js
 * 작업 관리(Work Management) 페이지 전용 스크립트
 */

let currentDetailId = null;

// [1] 상세 정보 로드 (우측 패널) - 변경 없음
function loadWorkDetail(workId, rowElem) {
    currentDetailId = workId;

    document.querySelectorAll('tr').forEach(r => r.classList.remove('table-active'));
    if(rowElem) rowElem.classList.add('table-active');

    const panel = document.getElementById('detailPanelBody');
    const actions = document.getElementById('detailActions');

    panel.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
    actions.classList.add('d-none');

    Promise.all([
        fetch(`/work/ajax/${workId}/detail`).then(r => r.json()),
        fetch(`/work/ajax/${workId}/attachments`).then(r => r.json())
    ])
    .then(([detailRes, attRes]) => {
        if(!detailRes.ok) throw new Error(detailRes.message);

        const d = detailRes.data;
        const attachments = attRes.items || [];

        let fileHtml = '<span class="text-muted small">첨부파일 없음</span>';
        if (attachments.length > 0) {
            fileHtml = `<ul class="list-group list-group-flush border rounded">` +
                attachments.map(f => `
                    <li class="list-group-item d-flex justify-content-between align-items-center bg-light p-2">
                        <a href="${f.url}" class="text-decoration-none text-dark text-truncate" style="max-width: 200px;">
                            <i class="bi bi-file-earmark me-1"></i>${f.name}
                        </a>
                        <span class="badge bg-secondary rounded-pill">${f.size}</span>
                    </li>`).join('') + `</ul>`;
        }

        panel.innerHTML = `
            <div class="mb-3">
                <label class="small fw-bold text-secondary">작업일</label>
                <div class="fs-5 fw-bold text-dark">${d.work_date}</div>
            </div>
            <div class="mb-3">
                <label class="small fw-bold text-secondary">유형</label>
                <div><span class="badge bg-primary bg-opacity-10 text-primary px-3 py-2">${d.work_type}</span></div>
            </div>
            <div class="mb-3">
                <label class="small fw-bold text-secondary">요약</label>
                <div class="fw-bold">${d.summary || '-'}</div>
            </div>
            <div class="mb-4">
                <label class="small fw-bold text-secondary">상세 내용</label>
                <div class="p-3 bg-light rounded border text-break" style="white-space: pre-wrap; min-height:100px;">${d.description || '-'}</div>
            </div>
            <div class="mb-3">
                <label class="small fw-bold text-secondary mb-2">첨부파일</label>
                <div>${fileHtml}</div>
            </div>
        `;
        actions.classList.remove('d-none');
    })
    .catch(err => {
        console.error(err);
        panel.innerHTML = `<div class="text-center text-danger py-4"><i class="bi bi-exclamation-triangle me-1"></i>정보를 불러오지 못했습니다.</div>`;
    });
}

// [2] 작업 등록
function openWorkCreateModal() {
    document.getElementById('workCreateForm').reset();
    const dateInput = document.querySelector('#workCreateForm [name="work_date"]');
    if(dateInput && !dateInput.value) dateInput.value = new Date().toISOString().split('T')[0];

    new bootstrap.Modal(document.getElementById('workCreateModal')).show();
}

async function createWork() {
    const form = document.getElementById('workCreateForm');
    if(!form.checkValidity()) { form.reportValidity(); return; }

    const formData = new FormData(form);

    try {
        const res = await fetch('/work/ajax/create', { method: 'POST', body: formData });
        const json = await res.json();

        if(json.ok) {
            await Swal.fire('성공', '작업이 등록되었습니다.', 'success');

            // [수정됨] 작업 탭 유지
            window.location.hash = 'tab-work';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch(e) {
        Swal.fire('오류', '통신 중 문제가 발생했습니다.', 'error');
    }
}

// [3] 작업 수정
function triggerEditFromDetail() {
    if(currentDetailId) openWorkEditModal(currentDetailId);
}

function openWorkEditModal(workId) {
    const modal = new bootstrap.Modal(document.getElementById('workEditModal'));
    const loading = document.getElementById('editLoading');
    const content = document.getElementById('editContent');

    document.getElementById('edit_work_id').value = workId;

    loading.style.display = 'block';
    content.style.display = 'none';
    modal.show();

    Promise.all([
        fetch(`/work/ajax/${workId}/detail`).then(r=>r.json()),
        fetch(`/work/ajax/${workId}/attachments`).then(r=>r.json())
    ]).then(([detailRes, attRes]) => {
        if(!detailRes.ok) throw new Error(detailRes.message);

        const d = detailRes.data;
        document.getElementById('edit_person_id').value = d.person_id;
        document.getElementById('edit_work_date').value = d.work_date;
        document.getElementById('edit_work_type').value = d.work_type;
        document.getElementById('edit_summary').value = d.summary || '';
        document.getElementById('edit_description').value = d.description || '';

        const fileList = document.getElementById('edit_file_list');
        const items = attRes.items || [];

        if(items.length > 0) {
            fileList.innerHTML = items.map(f => `
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom last-border-0">
                    <div class="text-truncate">
                        <i class="bi bi-file-earmark me-1"></i>${f.name} <small class="text-muted ms-1">(${f.size})</small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger" style="font-size: 0.75rem;" onclick="deleteAttachment(${f.id}, ${workId})">삭제</button>
                </div>
            `).join('');
        } else {
            fileList.innerHTML = '<span class="text-muted small">등록된 파일이 없습니다.</span>';
        }

        loading.style.display = 'none';
        content.style.display = 'block';
    }).catch(e => {
        modal.hide();
        Swal.fire('오류', '데이터를 불러오지 못했습니다.', 'error');
    });
}

async function updateWork() {
    const form = document.getElementById('workEditForm');
    const workId = document.getElementById('edit_work_id').value;
    const formData = new FormData(form);

    try {
        const res = await fetch(`/work/ajax/${workId}/update`, { method: 'POST', body: formData });
        const json = await res.json();

        if(json.ok) {
            await Swal.fire('수정 완료', '작업 정보가 수정되었습니다.', 'success');

            // [수정됨] 작업 탭 유지
            window.location.hash = 'tab-work';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch(e) {
        Swal.fire('오류', '통신 오류', 'error');
    }
}

// [4] 첨부파일 개별 삭제 (수정 모달 내부) - 변경 없음 (새로고침 안함)
async function deleteAttachment(attId, workId) {
    const result = await Swal.fire({
        title: '파일 삭제',
        text: "이 첨부파일을 삭제하시겠습니까?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: '삭제',
        cancelButtonText: '취소'
    });

    if(!result.isConfirmed) return;

    try {
        const res = await fetch(`/work/ajax/attachments/${attId}/delete`, { method: 'POST' });
        const json = await res.json();
        if(json.ok) {
            const attRes = await fetch(`/work/ajax/${workId}/attachments`).then(r=>r.json());
            const fileList = document.getElementById('edit_file_list');
            const items = attRes.items || [];

            if(items.length > 0) {
                fileList.innerHTML = items.map(f => `
                    <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom last-border-0">
                        <div class="text-truncate">
                            <i class="bi bi-file-earmark me-1"></i>${f.name} <small class="text-muted ms-1">(${f.size})</small>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" style="font-size: 0.75rem;" onclick="deleteAttachment(${f.id}, ${workId})">삭제</button>
                    </div>
                `).join('');
            } else {
                fileList.innerHTML = '<span class="text-muted small">등록된 파일이 없습니다.</span>';
            }
        } else {
            Swal.fire('실패', '파일 삭제에 실패했습니다.', 'error');
        }
    } catch(e) {
        Swal.fire('오류', '통신 오류', 'error');
    }
}

// [5] 작업 삭제
async function deleteWork(workId) {
    const result = await Swal.fire({
        title: '정말 삭제하시겠습니까?',
        text: "삭제된 작업과 첨부파일은 복구할 수 없습니다.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: '삭제',
        cancelButtonText: '취소'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/work/ajax/${workId}/delete`, { method: 'POST' });
            const json = await res.json();

            if(json.ok) {
                await Swal.fire('삭제됨', '작업이 삭제되었습니다.', 'success');

                // [수정됨] 작업 탭 유지
                window.location.hash = 'tab-work';
                window.location.reload();
            } else {
                Swal.fire('오류', json.message, 'error');
            }
        } catch(e) {
            Swal.fire('오류', '통신 오류', 'error');
        }
    }
}