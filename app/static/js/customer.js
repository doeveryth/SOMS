/**
 * customer.js
 * 고객 상세 페이지(detail.html) 전용 스크립트
 * - 고객 정보 수정
 * - 보안장비(Assets), 서버(Servers), 담당자(Contacts) 관리
 * - 작업 이력(Work) 관리 (고객 상세 페이지 내)
 */

document.addEventListener("DOMContentLoaded", function() {
    // -------------------------------------------------------------
    // [핵심] 페이지 로드 시 URL 해시(#tab-...)에 따라 탭 활성화
    // -------------------------------------------------------------
    var hash = window.location.hash; // 예: "#tab-work"

    if (hash) {
        // 1. 해당 해시를 타겟으로 하는 탭 버튼 찾기
        var triggerEl = document.querySelector('button[data-bs-target="' + hash + '"]');

        if (triggerEl) {
            // 2. [중요] 기존에 활성화된 탭(보통 대시보드)의 active 클래스 모두 제거
            document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('show', 'active'));

            // 3. 타겟 탭 버튼 활성화
            triggerEl.classList.add('active');

            // 4. 타겟 탭 내용 활성화
            var targetPane = document.querySelector(hash);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        }
    }

    // 보안장비 수정 모달 Select2 초기화
    const assetEditModal = document.getElementById('assetEditModal');
    if (assetEditModal && typeof $ !== 'undefined' && $.fn.select2) {
        assetEditModal.addEventListener('shown.bs.modal', function () {
            $('#edit_type').select2({ theme: 'bootstrap-5', dropdownParent: $('#assetEditModal'), width: '100%' });
            $('#edit_item').select2({ theme: 'bootstrap-5', dropdownParent: $('#assetEditModal'), width: '100%', placeholder: '선택 (선택사항)', allowClear: true });
            $('#edit_supplier').select2({ theme: 'bootstrap-5', dropdownParent: $('#assetEditModal'), width: '100%' });
            $('#edit_maintenance_company').select2({ theme: 'bootstrap-5', dropdownParent: $('#assetEditModal'), width: '100%' });
        });
    }
});
// ==============================================================
// [1] 고객 정보 (Customer Info)
// ==============================================================
// [1] 고객 정보 수정 모달 열기
function openCustomerEditModal() {
    new bootstrap.Modal(document.getElementById('customerEditModal')).show();
}

// [고객 정보 수정] AJAX + SweetAlert
async function updateCustomerInfo() {
    const form = document.getElementById('customerEditForm');
    const personId = document.getElementById('cust_person_id').value;
    const formData = new FormData(form);

    try {
        const res = await fetch(`/customers/${personId}/update`, {
            method: 'POST',
            body: formData
        });
        const json = await res.json();

        if (json.ok) {
            await Swal.fire({
                icon: 'success',
                title: '수정 완료',
                text: '고객 정보가 성공적으로 수정되었습니다.',
                confirmButtonText: '확인'
            });

            // [핵심 수정] 새로고침 전에 '대시보드 탭'을 보겠다고 명시
            window.location.hash = 'tab-overview';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        console.error(e);
        Swal.fire('오류', '통신 중 문제가 발생했습니다.', 'error');
    }
}

// [추가] 페이지 로드 시 탭 유지 기능 (대시보드 포함)
document.addEventListener("DOMContentLoaded", function() {
    // URL 해시값(#tab-...)을 읽어서 해당 탭을 활성화
    var hash = window.location.hash;
    if (hash) {
        var triggerEl = document.querySelector('button[data-bs-target="' + hash + '"]');
        if (triggerEl) {
            var tab = new bootstrap.Tab(triggerEl);
            tab.show();
        }
    }
});



// ==============================================================
// [2] 보안장비 (Assets)
// ==============================================================


function openAssetEditModal(btn) {
    // 1. 버튼의 data 속성에서 값 가져오기
    const d = btn.dataset;

    // 2. 모달의 입력 필드에 값 할당
    document.getElementById('edit_ci_name').value = d.name || '';
    document.getElementById('edit_supplier').value = d.supplier || '';
    document.getElementById('edit_category').value = d.category || '보안장비';
    document.getElementById('edit_type').value = d.type || '';
    document.getElementById('edit_item').value = d.item || '';
    document.getElementById('edit_product_name').value = d.product || '';
    document.getElementById('edit_model_number').value = d.model || '';
    document.getElementById('edit_manufacturer_name').value = d.manufacturer || '';

    document.getElementById('edit_serial_number').value = d.serial || '';
    document.getElementById('edit_ip_info').value = d.ip || '';
    document.getElementById('edit_ci_note').value = d.note || '';

    document.getElementById('edit_maintenance_company').value = d.maint || '11';
    document.getElementById('edit_operation_company').value = d.opComp || '0';
    document.getElementById('edit_operation_mode').value = d.opMode || '0';
    document.getElementById('edit_idc_site').value = d.idc || '';

    document.getElementById('edit_c_backup').value = d.backup || '0';
    document.getElementById('edit_c_cycle').value = d.cycle || '2';
    document.getElementById('edit_cfg_note').value = d.cnote || '';

    document.getElementById('edit_lifecycle_status').value = d.status || '3';

    // 날짜 필드 (값이 없으면 빈 문자열)
    document.getElementById('edit_installation_date').value = d.install && d.install != 'None' ? d.install.split(' ')[0] : '';
    document.getElementById('edit_license_expiry').value = d.license && d.license != 'None' ? d.license.split(' ')[0] : '';
    document.getElementById('edit_disposal_date').value = d.disposal && d.disposal != 'None' ? d.disposal.split(' ')[0] : '';

    document.getElementById('edit_description').value = d.desc || '';

    // 3. Form Action 업데이트 (수정 URL 설정) - URL은 상황에 맞게 조정 필요
    // 여기서는 asset_id를 경로에 포함시키는 방식 예시입니다.
    const form = document.getElementById('assetEditForm');
    // 예: /customers/P-1234/asset/update/1
    form.action = "{{ url_for('customers.detail', person_id=people.Person_ID) }}".replace('/detail', '') + '/asset/update/' + d.id;

    // 4. 모달 띄우기
    new bootstrap.Modal(document.getElementById('assetEditModal')).show();
}

// 상세 조회 모달 열기
function openAssetDetailModal(row) {
    const d = row.dataset;

    // --- 텍스트 변환 헬퍼 함수 ---
    const getOpName = (val) => (val == '0' ? 'ICTIS' : (val == '1' ? '고객사' : '-'));
    const getMaintName = (val) => {
        if(val=='0') return 'ICTIS';
        if(val=='11') return '고객사 유지보수';
        if(val=='12') return '없음';
        if(val=='13') return '윈스';
        return val || '-';
    };
    // [수정] 영어 제거 (탐지/차단만 표시)
    const getOpMode = (val) => {
        if(val == '1') return '탐지';
        if(val == '2') return '차단';
        return '해당 없음';
    };
    const getBackupYN = (val) => (val == '0' ? 'YES' : 'NO');
    const getBackupCycle = (val) => {
        if(val == '0') return 'Daily';
        if(val == '1') return 'Weekly';
        if(val == '2') return 'Monthly';
        return '-';
    };
    const getDate = (val) => (val && val != 'None' ? val.split(' ')[0] : '-');

    // --- 값 할당 (View) ---

    document.getElementById('view_name').innerText = d.name;
    document.getElementById('view_full_category').innerText = `${d.category} > ${d.type}` + (d.item ? ` > ${d.item}` : '');

    // [수정] 고객사 정보 (Jinja 오류 해결: dataset에서 가져옴)
    const companyInfo = (d.company || '') + ' / ' + (d.site || '');
    document.getElementById('view_customer_info').innerText = companyInfo;

    document.getElementById('view_manufacturer').innerText = d.manufacturer || '-';
    document.getElementById('view_product').innerText = d.product || '-';
    document.getElementById('view_model').innerText = d.model || '-';
    document.getElementById('view_serial').innerText = d.serial || '-';
    document.getElementById('view_ip').innerText = d.ip || '-';

    document.getElementById('view_maint').innerText = getMaintName(d.maint);
    document.getElementById('view_op_comp').innerText = getOpName(d.opComp);
    document.getElementById('view_op_mode').innerText = getOpMode(d.opMode);
    document.getElementById('view_supplier').innerText = d.supplier || '-';
    document.getElementById('view_idc').innerText = d.idc || '-';

    document.getElementById('view_backup_yn').innerText = getBackupYN(d.backup);
    document.getElementById('view_backup_cycle').innerText = getBackupCycle(d.cycle);
    document.getElementById('view_backup_note').innerText = d.cnote || '-';

    document.getElementById('view_install').innerText = getDate(d.install);
    document.getElementById('view_license').innerText = getDate(d.license);
    document.getElementById('view_disposal').innerText = getDate(d.disposal);

    document.getElementById('view_ci_note').innerText = d.note || '-';
    document.getElementById('view_desc').innerText = d.desc || '-';

    document.getElementById('view_submitter').innerText = d.submitter || '-';
    document.getElementById('view_updated').innerText = d.updated || '-';

    // 상태 배지 스타일링
    const statusEl = document.getElementById('view_status_badge');
    const statusMap = {'3':'사용중', '0':'주문됨', '1':'입고됨', '11':'폐기'};

    statusEl.className = 'badge rounded-pill px-3 py-2 me-2';
    if(d.status == '3') statusEl.classList.add('bg-success');
    else if(d.status == '0') statusEl.classList.add('bg-secondary');
    else if(d.status == '1') statusEl.classList.add('bg-info', 'text-dark');
    else if(d.status == '11') statusEl.classList.add('bg-danger');
    else statusEl.classList.add('bg-dark');

    statusEl.innerText = statusMap[d.status] || d.status;

    // 수정 버튼 이벤트 연결
    const goToEditHandler = function() {
        bootstrap.Modal.getInstance(document.getElementById('assetDetailModal')).hide();
        openAssetEditModalFromRow(row);
    };

    document.getElementById('btn_go_to_edit_top').onclick = goToEditHandler;
    //document.getElementById('btn_go_to_edit_bottom').onclick = goToEditHandler;

    new bootstrap.Modal(document.getElementById('assetDetailModal')).show();
}

// 수정 모달 열기 함수
function openAssetEditModalFromRow(row) {
    const d = row.dataset;

    // 1. 일반 input 값 할당
    document.getElementById('edit_ci_name').value = d.name || '';
    document.getElementById('edit_category').value = d.category || '보안장비';

    // 2. Select2 적용 필드는 jQuery로 값 변경 + trigger('change')
    $('#edit_supplier').val(d.supplier || '').trigger('change');
    $('#edit_type').val(d.type || '').trigger('change');
    $('#edit_item').val(d.item || '').trigger('change');
    $('#edit_maintenance_company').val(d.maint || '12').trigger('change'); // 기본값 12(없음)

    // 3. 나머지 값 할당
    document.getElementById('edit_product_name').value = d.product || '';
    document.getElementById('edit_model_number').value = d.model || '';
    document.getElementById('edit_manufacturer_name').value = d.manufacturer || '';
    document.getElementById('edit_serial_number').value = d.serial || '';
    document.getElementById('edit_ip_info').value = d.ip || '';
    document.getElementById('edit_ci_note').value = d.note || '';
    document.getElementById('edit_operation_company').value = d.opComp || '0';
    document.getElementById('edit_operation_mode').value = d.opMode || '0';
    document.getElementById('edit_idc_site').value = d.idc || '';
    document.getElementById('edit_c_backup').value = d.backup || '0';
    document.getElementById('edit_c_cycle').value = d.cycle || '2';
    document.getElementById('edit_cfg_note').value = d.cnote || '';
    document.getElementById('edit_lifecycle_status').value = d.status || '3';

    // 날짜 처리
    const parseDate = (val) => (val && val != 'None' ? val.split(' ')[0] : '');
    document.getElementById('edit_installation_date').value = parseDate(d.install);
    document.getElementById('edit_license_expiry').value = parseDate(d.license);
    document.getElementById('edit_disposal_date').value = parseDate(d.disposal);
    document.getElementById('edit_description').value = d.desc || '';

    // [핵심 수정] Action URL 업데이트 (Jinja 제거 및 라우트 경로 일치시킴)
    // Python Route: @bp.post("/<person_id>/ci/<int:asset_id>/edit")
    const form = document.getElementById('assetEditForm');

    // '/customers/' 경로는 블루프린트 설정에 따라 다를 수 있으나 보통 customers를 씁니다.
    // 만약 URL이 다르다면 '/customers/' 부분을 실제 prefix로 바꿔주세요.
    form.action = '/customers/' + d.personId + '/ci/' + d.id + '/edit';

    // 모달 띄우기
    new bootstrap.Modal(document.getElementById('assetEditModal')).show();
}

// 보안장비 수정 모달 열기
async function editAsset(assetId, personId) {
    const modal = new bootstrap.Modal(document.getElementById('assetEditModal'));
    const form = document.getElementById('assetEditForm');
    const body = document.getElementById('assetEditBody');

    try {
        const res = await fetch(`/customers/${personId}/ci/${assetId}/edit`);
        const data = await res.json();

        if (!data.ok) {
            alert(data.message || '로드에 실패했습니다.');
            return;
        }

        const d = data.data;
        body.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">분류</label>
          <input type="text" class="form-control" name="category" value="${d.category || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">유형</label>
          <input type="text" class="form-control" name="type" value="${d.type || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">품목</label>
          <input type="text" class="form-control" name="item" value="${d.item || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">모델명</label>
          <input type="text" class="form-control" name="model_number" value="${d.model_number || ''}">
        </div>
        <div class="col-12">
          <label class="form-label">설명</label>
          <textarea class="form-control" name="description" rows="3">${d.description || ''}</textarea>
        </div></div>
    `;

        form.action = `/customers/${personId}/ci/${assetId}/edit`;
        modal.show();
    } catch (err) {
        alert('로드에 실패했습니다.');
    }
}
//장비 삭제
document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('assetDeleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            // 버튼에서 데이터 가져오기
            const button = event.relatedTarget;
            const deleteUrl = button.getAttribute('data-url');
            const assetName = button.getAttribute('data-name');

            // 모달 내부 텍스트 및 폼 액션 업데이트
            const form = deleteModal.querySelector('#assetDeleteForm');
            const nameDisplay = deleteModal.querySelector('#deleteAssetName');

            form.action = deleteUrl;
            nameDisplay.textContent = assetName;
        });
    }
});

// ==============================================================
// [3] 서버 (Servers)
// ==============================================================

// [1] 서버 추가 모달 열기
function openServerAddModal() {
    new bootstrap.Modal(document.getElementById('serverAddModal')).show();
}

// [2] 행 추가/삭제 로직 (기존 유지)
function addServerRow() {
    const container = document.getElementById('serverEntryContainer');
    const newRow = document.createElement('div');
    newRow.className = 'card border-0 shadow-sm mb-2 server-row';
    newRow.innerHTML = `
        <div class="card-body p-2">
            <div class="row g-2 align-items-center">
                <div class="col-6">
                    <div class="form-floating">
                        <input type="text" class="form-control border-0 bg-light" name="server_names[]" placeholder="서버명" required>
                        <label>서버명 <span class="text-danger">*</span></label>
                    </div>
                </div>
                <div class="col">
                    <div class="form-floating">
                        <input type="text" class="form-control border-0 bg-light" name="server_ips[]" placeholder="IP 주소">
                        <label>서버 IP</label>
                    </div>
                </div>
                <div class="col-auto">
                    <button type="button" class="btn btn-outline-danger d-flex align-items-center justify-content-center" 
                            style="height: 58px; width: 50px;" onclick="removeServerRow(this)">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>`;
    container.appendChild(newRow);
}
function removeServerRow(btn) { btn.closest('.server-row').remove(); }

// [3] 서버 추가 (AJAX + SweetAlert)
async function addServer() {
    const form = document.getElementById('serverAddForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }

    const personId = document.getElementById('server_person_id').value;
    const formData = new FormData(form);

    try {
        const res = await fetch(`/customers/${personId}/servers/add`, { method: 'POST', body: formData });
        const json = await res.json();

        if (json.ok) {
            await Swal.fire('성공', json.message, 'success');
            window.location.hash = 'tab-servers';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        Swal.fire('오류', '통신 오류', 'error');
    }
}

// [4] 서버 수정 모달 열기 (데이터 로드)
async function editServer(serverId, personId) {
    const modal = new bootstrap.Modal(document.getElementById('serverEditModal'));
    const body = document.getElementById('serverEditBody');

    body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';
    modal.show();

    try {
        const res = await fetch(`/customers/${personId}/servers/${serverId}/edit`);
        const json = await res.json();

        if (!json.ok) { alert(json.message); modal.hide(); return; }

        const s = json.data;
        body.innerHTML = `
            <input type="hidden" id="edit_server_id" value="${s.id}">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-12">
                            <label class="form-label fw-bold small text-secondary">서버명 <span class="text-danger">*</span></label>
                            <input type="text" class="form-control" name="server_name" id="edit_server_name" value="${s.server_name}" required>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-bold small text-secondary">서버 IP</label>
                            <input type="text" class="form-control" name="server_ip" id="edit_server_ip" value="${s.server_ip || ''}">
                        </div>
                    </div>
                </div>
            </div>`;
    } catch (e) {
        console.error(e);
        modal.hide();
    }
}

// [5] 서버 수정 저장 (SweetAlert 적용!)
async function updateServer() {
    const form = document.getElementById('serverEditForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }

    const personId = document.getElementById('server_person_id').value;
    const serverId = document.getElementById('edit_server_id').value;

    // FormData 생성
    const formData = new FormData();
    formData.append('server_name', document.getElementById('edit_server_name').value);
    formData.append('server_ip', document.getElementById('edit_server_ip').value);

    try {
        const res = await fetch(`/customers/${personId}/servers/${serverId}/edit`, {
            method: 'POST', body: formData
        });
        const json = await res.json();

        if (json.ok) {
            // [성공 시 SweetAlert]
            await Swal.fire({
                icon: 'success',
                title: '수정 완료',
                text: '서버 정보가 수정되었습니다.',
                confirmButtonText: '확인'
            });
            window.location.hash = 'tab-servers';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        Swal.fire('오류', '통신 중 오류가 발생했습니다.', 'error');
    }
}

// [6] 서버 삭제 (SweetAlert 적용!)
async function deleteServer(serverId, personId) {
    // [삭제 전 확인창]
    const result = await Swal.fire({
        title: '삭제하시겠습니까?',
        text: "선택한 서버 정보가 영구적으로 삭제됩니다.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '삭제',
        cancelButtonText: '취소'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/customers/${personId}/servers/${serverId}/delete`, {
                method: 'POST'
            });
            const json = await res.json();

            if (json.ok) {
                // [성공 시 SweetAlert]
                await Swal.fire('삭제됨', '서버가 삭제되었습니다.', 'success');
                window.location.hash = 'tab-servers';
                window.location.reload();
            } else {
                Swal.fire('오류', json.message, 'error');
            }
        } catch (e) {
            Swal.fire('오류', '삭제 중 문제가 발생했습니다.', 'error');
        }
    }
}

// [7] 탭 유지
document.addEventListener("DOMContentLoaded", function() {
    if (window.location.hash === '#tab-servers') {
        const triggerEl = document.querySelector('button[data-bs-target="#tab-servers"]');
        if (triggerEl) new bootstrap.Tab(triggerEl).show();
    }
});

// ==============================================================
// [4] 담당자 (Contacts)
// ==============================================================


// [1] 담당자 추가 모달 열기
function openContactAddModal() {
    new bootstrap.Modal(document.getElementById('contactAddModal')).show();
}

// [2] 담당자 등록 (AJAX + SweetAlert)
async function addContact() {
    const form = document.getElementById('contactAddForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }

    const personId = document.getElementById('contact_person_id').value;
    const url = `/customers/${personId}/contacts/add`;
    const formData = new FormData(form);

    try {
        const res = await fetch(url, { method: 'POST', body: formData });
        const json = await res.json();

        if (json.ok) {
            await Swal.fire('성공', '담당자가 등록되었습니다.', 'success');
            window.location.hash = 'tab-contacts';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        Swal.fire('오류', '통신 중 오류가 발생했습니다.', 'error');
    }
}

// [3] 담당자 수정 모달 열기 & 데이터 바인딩
async function openContactEditModal(contactId, personId) {
    try {
        const res = await fetch(`/customers/${personId}/contacts/${contactId}/edit`);
        const json = await res.json();

        if (json.ok) {
            const data = json.data;
            // 데이터 바인딩
            document.getElementById('edit_contact_id').value = data.id;
            document.getElementById('edit_role_type').value = data.role;
            document.getElementById('edit_name').value = data.name;
            document.getElementById('edit_general_phone').value = data.gen_phone;
            document.getElementById('edit_phone').value = data.phone;
            document.getElementById('edit_email').value = data.email;
            document.getElementById('edit_status').value = data.status;
            document.getElementById('edit_sms_yn').value = data.sms_yn;
            document.getElementById('edit_report_yn').value = data.report_yn;

            new bootstrap.Modal(document.getElementById('contactEditModal')).show();
        } else {
            Swal.fire('오류', '정보를 불러오지 못했습니다.', 'error');
        }
    } catch (e) {
        console.error(e);
    }
}

// [4] 담당자 수정 저장 (SweetAlert 적용됨)
async function updateContact() {
    const form = document.getElementById('contactEditForm');

    // 유효성 검사 (빈칸 체크)
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const personId = document.getElementById('contact_person_id').value;
    const contactId = document.getElementById('edit_contact_id').value;
    const formData = new FormData(form);

    try {
        const res = await fetch(`/customers/${personId}/contacts/${contactId}/edit`, {
            method: 'POST', body: formData
        });
        const json = await res.json();

        if (json.ok) {
            // [핵심] 작업 탭과 똑같은 성공 팝업 띄우기!
            await Swal.fire({
                icon: 'success',           // 체크 표시 아이콘
                title: '수정 완료',         // 제목
                text: '담당자 정보가 수정되었습니다.', // 내용
                confirmButtonText: 'OK',   // 버튼 텍스트
                confirmButtonColor: '#3085d6' // 버튼 색상 (파랑)
            });

            // 확인 버튼 누르면 탭 유지하면서 새로고침
            window.location.hash = 'tab-contacts';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        Swal.fire('오류', '통신 중 문제가 발생했습니다.', 'error');
    }
}

// [5] 담당자 삭제 (SweetAlert Warning)
async function deleteContact(contactId, personId) {
    // 사용자가 보여준 이미지와 동일한 디자인의 경고창
    const result = await Swal.fire({
        title: '삭제하시겠습니까?',
        text: "선택한 담당자가 삭제됩니다.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545', // 빨간색
        cancelButtonColor: '#6c757d',  // 회색
        confirmButtonText: '삭제',
        cancelButtonText: '취소'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/customers/${personId}/contacts/${contactId}/delete`, {
                method: 'POST'
            });
            const json = await res.json();

            if (json.ok) {
                await Swal.fire('삭제됨', '삭제되었습니다.', 'success');
                window.location.hash = 'tab-contacts';
                window.location.reload();
            } else {
                Swal.fire('오류', json.message, 'error');
            }
        } catch (e) {
            Swal.fire('오류', '삭제 중 문제가 발생했습니다.', 'error');
        }
    }
}

// [6] 탭 유지
document.addEventListener("DOMContentLoaded", function() {
    if (window.location.hash === '#tab-contacts') {
        const triggerEl = document.querySelector('button[data-bs-target="#tab-contacts"]');
        if (triggerEl) {
            new bootstrap.Tab(triggerEl).show();
        }
    }
});




// ==============================================================
// [5] 작업 이력 (Work History) - detail.html 전용
// ==============================================================

// 1. 작업 등록 (AJAX)
async function createWork() {
    const form = document.getElementById('workCreateForm');
    if(!form.checkValidity()) { form.reportValidity(); return; }

    const formData = new FormData(form);

    // 날짜 값 없으면 오늘 날짜 자동 입력 (안전장치)
    if(!formData.get('work_date')) {
        formData.set('work_date', new Date().toISOString().split('T')[0]);
    }

    try {
        // work.py의 공통 API 호출
        const res = await fetch('/work/ajax/create', { method: 'POST', body: formData });
        const json = await res.json();

        if(json.ok) {
            await Swal.fire('성공', '작업이 등록되었습니다.', 'success');
            window.location.hash = 'tab-work'; // 작업 탭 유지
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch(e) {
        Swal.fire('오류', '통신 중 문제가 발생했습니다.', 'error');
    }
}

// 2. 작업 수정 모달 열기 (데이터 로드)
function openWorkEditModal(workId) {
    const modal = new bootstrap.Modal(document.getElementById('workEditModal'));
    const loading = document.getElementById('editLoading');
    const content = document.getElementById('editContent');

    document.getElementById('edit_work_id').value = workId;
    loading.style.display = 'block';
    content.style.display = 'none';
    modal.show();

    // work.py의 공통 API 재사용
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

        // 첨부파일 렌더링
        const fileList = document.getElementById('edit_file_list');
        const items = attRes.items || [];

        if(items.length > 0) {
            fileList.innerHTML = items.map(f => `
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom last-border-0">
                    <div class="text-truncate">
                        <i class="bi bi-file-earmark me-1"></i>${f.name} <small class="text-muted ms-1">(${f.size})</small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger" style="font-size: 0.75rem;" onclick="deleteAttachmentInCustomer(${f.id}, ${workId})">삭제</button>
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

// 3. 첨부파일 개별 삭제 (수정 모달 내)
async function deleteAttachmentInCustomer(attId, workId) {
    if(!confirm("이 첨부파일을 삭제하시겠습니까?")) return;

    try {
        const res = await fetch(`/work/ajax/attachments/${attId}/delete`, { method: 'POST' });
        const json = await res.json();
        if(json.ok) {
            // 모달 닫지 않고 파일 목록만 새로고침 (UX 향상)
            const attRes = await fetch(`/work/ajax/${workId}/attachments`).then(r=>r.json());
            const fileList = document.getElementById('edit_file_list');
            const items = attRes.items || [];

            if(items.length > 0) {
                fileList.innerHTML = items.map(f => `
                    <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom last-border-0">
                        <div class="text-truncate">
                            <i class="bi bi-file-earmark me-1"></i>${f.name} <small class="text-muted ms-1">(${f.size})</small>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" style="font-size: 0.75rem;" onclick="deleteAttachmentInCustomer(${f.id}, ${workId})">삭제</button>
                    </div>
                `).join('');
            } else {
                fileList.innerHTML = '<span class="text-muted small">등록된 파일이 없습니다.</span>';
            }
        } else {
            alert('삭제 실패');
        }
    } catch(e) {
        alert('통신 오류');
    }
}


// 4. 작업 수정 저장
async function updateWork() {
    const form = document.getElementById('workEditForm');
    const workId = document.getElementById('edit_work_id').value;
    const formData = new FormData(form);

    try {
        const res = await fetch(`/work/ajax/${workId}/update`, { method: 'POST', body: formData });
        const json = await res.json();

        if(json.ok) {
            await Swal.fire('수정 완료', '작업 정보가 수정되었습니다.', 'success');

            // [핵심 수정] 작업 탭을 보겠다고 명시한 뒤 새로고침
            window.location.hash = 'tab-work';
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch(e) {
        Swal.fire('오류', '통신 오류', 'error');
    }
}

// 5. 작업 삭제 (SweetAlert)
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

    if(result.isConfirmed) {
        try {
            const res = await fetch(`/work/ajax/${workId}/delete`, { method: 'POST' });
            const json = await res.json();

            if(json.ok) {
                await Swal.fire('삭제됨', '작업이 삭제되었습니다.', 'success');
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

// 6. 작업 상세 조회 (리스트 클릭 시)
function openWorkDetail(workId) {
    const modal = new bootstrap.Modal(document.getElementById('workDetailModal'));
    const body = document.getElementById('workDetailBody');

    body.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
    modal.show();

    Promise.all([
        fetch(`/work/ajax/${workId}/detail`).then(r=>r.json()),
        fetch(`/work/ajax/${workId}/attachments`).then(r=>r.json())
    ]).then(([detailRes, attRes]) => {
        if(!detailRes.ok) throw new Error(detailRes.message);

        const d = detailRes.data;
        const items = attRes.items || [];

        let fileHtml = '<span class="text-muted small">첨부파일 없음</span>';
        if(items.length > 0) {
            fileHtml = `<ul class="list-group">` +
                items.map(f => `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <a href="${f.url}" class="text-decoration-none text-dark">
                            <i class="bi bi-file-earmark me-2"></i>${f.name}
                        </a>
                        <span class="badge bg-secondary rounded-pill">${f.size}</span>
                    </li>
                `).join('') + `</ul>`;
        }

        body.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6"><label class="small fw-bold text-secondary">작업일</label><div>${d.work_date}</div></div>
                <div class="col-md-6"><label class="small fw-bold text-secondary">유형</label><div><span class="badge bg-primary bg-opacity-10 text-primary">${d.work_type}</span></div></div>
                <div class="col-12"><label class="small fw-bold text-secondary">요약</label><div class="fw-bold">${d.summary || '-'}</div></div>
                <div class="col-12"><label class="small fw-bold text-secondary">상세정보</label><div class="p-3 bg-light rounded border" style="white-space: pre-wrap;">${d.description || '-'}</div></div>
                <div class="col-12"><label class="small fw-bold text-secondary mb-2">첨부파일</label><div>${fileHtml}</div></div>
            </div>
        `;
    }).catch(e => {
        body.innerHTML = '<div class="text-center text-danger py-4">정보를 불러오지 못했습니다.</div>';
    });
}