const assetModal = new bootstrap.Modal(document.getElementById('assetModal'));
    const assetDetailModal = new bootstrap.Modal(document.getElementById('assetDetailModal'));
    let currentRow = null;

    // [중요] Select2 초기화 (모든 .select2-site 클래스에 적용)
    $(document).ready(function() {
        $('.select2-site').select2({
            theme: 'bootstrap-5',
            dropdownParent: $('#assetModal'), // 모달 내에서 동작 보장
            width: '100%',
            placeholder: "선택하세요"
        });

        // 고객사 자동 입력 (사이트명 변경 시)
        $('#person_id').on('change', function() {
            const selectedOption = $(this).find(':selected');
            const company = selectedOption.data('company');
            $('#display_company').val(company || '');
        });
    });

    // 1. 상세 조회 (Read Only) - 변경 없음
    function openAssetDetailModal(tr) {
        currentRow = tr;
        const d = tr.dataset;

        // (기존 상세 매핑 로직 유지)
        document.getElementById('view_ci_name').innerText = d.ciName || '-';
        document.getElementById('view_company').innerText = d.company || '-';
        document.getElementById('view_site').innerText = d.site || '-';
        document.getElementById('view_serial').innerText = d.serialNumber || '-';
        document.getElementById('view_ip').innerText = d.ipInfo || '-';
        document.getElementById('view_os').innerText = d.osVersion || '-';
        document.getElementById('view_supplier').innerText = d.supplier || '-';
        document.getElementById('view_type').innerText = d.type || '-';
        document.getElementById('view_product_model').innerText = (d.productName || '') + ' / ' + (d.modelNumber || '');
        document.getElementById('view_manufacturer').innerText = d.manufacturerName || '-';

        let modeText = '-';
        if(d.operationMode == '1') modeText = '탐지';
        else if(d.operationMode == '2') modeText = '차단';
        document.getElementById('view_op_mode').innerText = modeText;

        document.getElementById('view_maint_comp').innerText = getCompanyName(d.maintenanceCompany);
        document.getElementById('view_op_comp').innerText = getCompanyName(d.operationCompany);
        document.getElementById('view_idc').innerText = d.idcSite || '-';

        document.getElementById('view_backup').innerText = d.cBackup == '0' ? 'YES' : 'NO';
        document.getElementById('view_cycle').innerText = getCycleName(d.cCycle);
        document.getElementById('view_cfg_note').innerText = d.cfgNote || '-';
        document.getElementById('view_install_date').innerText = d.installationDate || '-';
        document.getElementById('view_expiry_date').innerText = d.licenseExpiry || '-';
        document.getElementById('view_desc').innerText = d.description || '-';

        document.getElementById('btnEditFromDetail').onclick = function() {
            assetDetailModal.hide();
            openAssetEditModalFromRow(tr);
        };

        assetDetailModal.show();
    }

    function getCompanyName(code) {
        const map = {
            '0': 'ICTIS', '11': '고객사 유지보수', '1': '에스에이정보기술', '2': '블루시큐어',
            '3': '유콘텍', '4': '유니포인트', '5': '엔큐리티', '6': '시큐트러스트',
            '7': '모니터랩', '8': '인스테크', '9': '쿼리시스템즈', '10': '에스디씨디엠',
            '12': '없음', '13': '윈스'
        };
        return map[code] || code || '-';
    }

    function getCycleName(code) {
        if(code == '0') return 'Daily';
        if(code == '1') return 'Weekly';
        if(code == '2') return 'Monthly';
        return '-';
    }

    // 2. 수정 모달 열기 (데이터 바인딩)
    function openAssetEditModalFromRow(tr) {
        document.getElementById('assetModalTitle').innerText = '장비 수정';
        document.getElementById('asset_id').value = tr.dataset.id;

        const d = tr.dataset;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if(el) el.value = (val === 'None' || val === undefined) ? '' : val;
        };

        // [중요] Select2 필드 값 설정 및 UI 갱신 (trigger change)
        if(d.personId) $('#person_id').val(d.personId).trigger('change');
        if(d.type) $('#type').val(d.type).trigger('change');
        if(d.item) $('#item').val(d.item).trigger('change');
        if(d.maintenanceCompany) $('#maintenance_company').val(d.maintenanceCompany).trigger('change');

        // 일반 필드 설정
        setVal('ci_name', d.ciName);
        setVal('supplier', d.supplier);
        setVal('category', d.category);
        setVal('product_name', d.productName);
        setVal('model_number', d.modelNumber);
        setVal('manufacturer_name', d.manufacturerName);
        setVal('serial_number', d.serialNumber);
        setVal('ip_address', d.ipInfo);
        setVal('os_version', d.osVersion);
        setVal('region', d.region);
        setVal('idc_site', d.idcSite);
        setVal('ci_note', d.ciNote);
        setVal('operation_company', d.operationCompany);
        setVal('operation_mode', d.operationMode);
        setVal('c_backup', d.cBackup);
        setVal('c_cycle', d.cCycle);
        setVal('cfg_note', d.cfgNote);
        setVal('lifecycle_status', d.lifecycleStatus);

        setVal('purchase_date', d.purchaseDate);
        setVal('installation_date', d.installationDate);
        setVal('license_expiry', d.licenseExpiry);
        setVal('disposal_date', d.disposalDate);
        setVal('description', d.description);

        assetModal.show();
    }

    // 3. 등록 모달 열기 (초기화)
    function openAssetRegisterModal() {
        document.getElementById('assetForm').reset();
        document.getElementById('assetModalTitle').innerText = '보안장비 추가';
        document.getElementById('asset_id').value = '';
        document.getElementById('display_company').value = '';

        // [중요] 모든 Select2 필드 초기화
        $('.select2-site').val('').trigger('change');

        assetModal.show();
    }

    // 4. 저장 (AJAX)
    async function saveAsset() {
        const form = document.getElementById('assetForm');
        if (!form.checkValidity()) { form.reportValidity(); return; }

        const formData = new FormData(form);

        try {
            const res = await fetch('/asset/ajax/save', { method: 'POST', body: formData });
            const json = await res.json();

            if (json.ok) {
                await Swal.fire('저장 완료', '정상적으로 저장되었습니다.', 'success');
                window.location.reload();
            } else {
                Swal.fire('오류', json.message, 'error');
            }
        } catch(e) {
            Swal.fire('오류', '통신 중 오류가 발생했습니다.', 'error');
        }
    }

    // 5. 삭제 (AJAX)
    async function deleteAsset(id) {
        const result = await Swal.fire({
            title: '삭제하시겠습니까?',
            text: "삭제 시 복구가 불가능할 수 있습니다.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: '삭제'
        });

        if (result.isConfirmed) {
            try {
                const res = await fetch(`/asset/ajax/${id}/delete`, { method: 'POST' });
                const json = await res.json();
                if (json.ok) {
                    await Swal.fire('삭제됨', '삭제되었습니다.', 'success');
                    window.location.reload();
                } else {
                    Swal.fire('오류', '삭제 실패', 'error');
                }
            } catch(e) {
                Swal.fire('오류', '통신 오류', 'error');
            }
        }
    }