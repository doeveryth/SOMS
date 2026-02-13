let dashAssetRow = null;

$(document).ready(function () {
    window.initializeSelect2 = function () {
    };

    $('.select2-dash').select2({
        theme: 'bootstrap-5',
        dropdownParent: $('#dashEditModal'),
        width: '100%',
        placeholder: "선택하세요"
    });

    $('#dash_person_id').on('change', function () {
        const selectedOption = $(this).find(':selected');
        const company = selectedOption.data('company');
        $('#dash_display_company').val(company || '');
    });
});

// 1. 상세 보기
function openDashDetail(row) {
    dashAssetRow = row;
    const d = row.dataset;

    document.getElementById('view_dash_name').innerText = d.name || '-';
    document.getElementById('view_dash_customer').innerText = (d.company || '') + ' / ' + (d.site || '');

    const st = d.status || '3';
    const stMap = {'3': '사용중', '0': '주문됨', '1': '입고됨', '11': '폐기'};
    const stCls = {'3': 'bg-success', '0': 'bg-secondary', '1': 'bg-info text-dark', '11': 'bg-danger'};
    const bdg = document.getElementById('view_dash_status');
    bdg.innerText = stMap[st] || st;
    bdg.className = `badge rounded-pill px-3 py-2 ${stCls[st] || 'bg-secondary'}`;

    document.getElementById('view_dash_ip').innerText = d.ip || '-';
    document.getElementById('view_dash_serial').innerText = d.serial || '-';
    document.getElementById('view_dash_category').innerText = (d.category || '') + (d.type ? ` > ${d.type}` : '');

    document.getElementById('view_dash_maker').innerText = d.manufacturer || '-';
    document.getElementById('view_dash_product').innerText = d.product || '-';
    document.getElementById('view_dash_model').innerText = d.model || '-';

    // 유지보수 매핑 (숫자 -> 텍스트)
    const maintMap = {
        '0': 'ICTIS', '1': '에스에이정보기술', '2': '블루시큐어', '3': '유콘텍', '4': '유니포인트', '5': '엔큐리티',
        '6': '시큐트러스트', '7': '모니터랩', '8': '인스테크', '9': '쿼리시스템즈', '10': '에스디씨디엠',
        '11': '고객사 유지보수', '12': '없음', '13': '윈스'
    };
    document.getElementById('view_dash_maint').innerText = maintMap[d.maint] || d.maint || '-';
    document.getElementById('view_dash_op_comp').innerText = (d.opComp == '0' ? 'ICTIS' : (d.opComp == '1' ? '고객사' : '-'));
    document.getElementById('view_dash_mode').innerText = (d.opMode == '1' ? '탐지' : (d.opMode == '2' ? '차단' : '-'));
    document.getElementById('view_dash_idc').innerText = d.idc || '-';
    document.getElementById('view_dash_supplier').innerText = d.supplier || '-';

    document.getElementById('view_dash_backup').innerText = (d.backup == '0' ? 'YES' : 'NO');
    document.getElementById('view_dash_cycle').innerText = (d.cycle == '0' ? 'Daily' : (d.cycle == '1' ? 'Weekly' : 'Monthly'));
    document.getElementById('view_dash_note').innerText = d.cnote || '';

    const pD = (v) => (v && v != 'None') ? v.split(' ')[0] : '-';
    document.getElementById('view_dash_purchase').innerText = pD(d.purchase);
    document.getElementById('view_dash_receive').innerText = pD(d.receive);
    document.getElementById('view_dash_install').innerText = pD(d.install);
    document.getElementById('view_dash_return').innerText = pD(d.return);
    document.getElementById('view_dash_disposal').innerText = pD(d.disposal);
    document.getElementById('view_dash_license').innerText = pD(d.license);

    document.getElementById('view_dash_desc').innerText = d.desc || '-';

    document.getElementById('view_dash_submitter').innerText = d.submitter || '-';
    document.getElementById('view_dash_updated').innerText = d.updated || '-';

    document.getElementById('btnDashEdit').onclick = function () {
        bootstrap.Modal.getInstance(document.getElementById('dashDetailModal')).hide();
        openDashEdit(row);
    };

    new bootstrap.Modal(document.getElementById('dashDetailModal')).show();
}

// 2. 등록
function openDashRegister() {
    document.getElementById('dashForm').reset(); // 폼 초기화 (사이트명 등 텍스트 필드 다 비워짐)
    document.getElementById('dashModalTitle').innerText = '보안장비 추가';
    document.getElementById('dash_asset_id').value = '';

    // [수정] select2 초기화 (고객사 선택 초기화)
    $('.select2-dash').val('').trigger('change');

    new bootstrap.Modal(document.getElementById('dashEditModal')).show();
}

// 3. 수정
function openDashEdit(tr) {
    document.getElementById('dashModalTitle').innerText = '보안장비 수정';
    document.getElementById('dash_asset_id').value = tr.dataset.id;

    const d = tr.dataset;
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = (val === 'None' || val === undefined) ? '' : val;
    };

    // [수정] 고객사(Select2) 값 설정
    if (d.personId) {
        $('#dash_person_id').val(d.personId).trigger('change');
    }

    // [추가됨] 사이트명 (Site Name) 값 설정
    // HTML tr 태그에 data-site="..." 속성이 있어야 함
    setVal('dash_owner_name', d.site);

    // 나머지 Select2 값 설정
    $('#dash_supplier').val(d.supplier).trigger('change');
    $('#dash_type').val(d.type).trigger('change');
    $('#dash_item').val(d.item).trigger('change');
    $('#dash_maintenance_company').val(d.maint).trigger('change');

    // 텍스트 필드 값 설정
    setVal('dash_ci_name', d.name);
    setVal('dash_category', d.category);
    setVal('dash_product_name', d.product);
    setVal('dash_model_number', d.model);
    setVal('dash_manufacturer_name', d.manufacturer);
    setVal('dash_serial_number', d.serial);
    setVal('dash_ip_address', d.ip);

    setVal('dash_ci_note', d.note);
    setVal('dash_operation_company', d.opComp);
    setVal('dash_operation_mode', d.opMode);
    setVal('dash_idc_site', d.idc);
    setVal('dash_c_backup', d.backup);
    setVal('dash_c_cycle', d.cycle);
    setVal('dash_cfg_note', d.cnote);
    setVal('dash_lifecycle_status', d.status);

    // 날짜 데이터 처리
    const pD = (v) => (v && v != 'None') ? v.split(' ')[0] : '';
    setVal('dash_purchase_date', pD(d.purchase));
    setVal('dash_receive_date', pD(d.receive));
    setVal('dash_installation_date', pD(d.install));
    setVal('dash_return_date', pD(d.return));
    setVal('dash_license_expiry', pD(d.license));
    setVal('dash_disposal_date', pD(d.disposal));

    setVal('dash_description', d.desc);

    new bootstrap.Modal(document.getElementById('dashEditModal')).show();
}
// 4. 저장
async function saveDashAsset() {
    const form = document.getElementById('dashForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const formData = new FormData(form);
    try {
        const res = await fetch('/asset/ajax/save', {method: 'POST', body: formData});
        const json = await res.json();

        if (json.ok) {
            bootstrap.Modal.getInstance(document.getElementById('dashEditModal')).hide();
            await Swal.fire('성공', '저장되었습니다.', 'success');
            window.location.reload();
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        Swal.fire('오류', '통신 중 문제가 발생했습니다.', 'error');
    }
}

// 5. 삭제
async function deleteDashAsset(id) {
    const result = await Swal.fire({
        title: '삭제하시겠습니까?',
        text: "복구할 수 없습니다.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: '삭제'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/asset/ajax/${id}/delete`, {method: 'POST'});
            const json = await res.json();
            if (json.ok) {
                await Swal.fire('삭제됨', '삭제되었습니다.', 'success');
                window.location.reload();
            } else {
                Swal.fire('오류', '삭제 실패', 'error');
            }
        } catch (e) {
            Swal.fire('오류', '통신 오류', 'error');
        }
    }
}


//서버
$(document).ready(function () {
    // [Select2] 등록 모달 내 사이트 검색 기능 활성화
    window.initializeSelect2 = function () {
    };
    $('.select2-server').select2({
        dropdownParent: $('#serverCreateModal'),
        theme: 'bootstrap-5',
        placeholder: "사이트를 검색하세요",
        width: '100%',
        allowClear: true
    });

    // [핵심 기능] 사이트 선택 시 고객사명 자동 입력
    $('#modal_person_id').on('change', function () {
        // 선택된 옵션의 data-company 속성 값을 가져옴
        const selectedOption = $(this).find(':selected');
        const companyName = selectedOption.data('company');

        // 고객사 Input 창에 값 넣기
        $('#modal_auto_company').val(companyName || '');
    });
});

// [상세 보기] 모달 열기 함수
function openServerDetail(row) {
    const d = row.dataset;

    document.getElementById('detail_name').innerText = d.name || '-';
    document.getElementById('detail_ip').innerText = d.ip || '-';
    document.getElementById('detail_customer').innerText = d.company || '-';
    document.getElementById('detail_site').innerText = d.site || '-';
    document.getElementById('detail_submitter').innerText = d.submitter || '-';
    document.getElementById('detail_created').innerText = d.created || '-';

    new bootstrap.Modal(document.getElementById('serverDetailModal')).show();
}

// [등록] 모달 열기
function openServerRegister() {
    // 모달 열 때 폼 리셋이 필요하면 여기서 처리
    $('#modal_person_id').val('').trigger('change');
    $('#modal_auto_company').val('');
    document.querySelector('#serverCreateModal form').reset();

    new bootstrap.Modal(document.getElementById('serverCreateModal')).show();
}