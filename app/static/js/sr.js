    const srModal = new bootstrap.Modal(document.getElementById('srModal'));
    const srDetailModal = new bootstrap.Modal(document.getElementById('srDetailModal'));

    // 사이트 선택 시 고객사 자동 입력
    function changeSite(selectElem) {
        const option = selectElem.options[selectElem.selectedIndex];
        const company = option.getAttribute('data-company');
        document.getElementById('edit_company').value = company || '';
    }

    // [1] SR 상세 조회 모달 열기
    async function openSrDetailModal(srId) {
        const body = document.getElementById('srDetailBody');
        const editBtn = document.getElementById('btnEditFromDetail');

        // 로딩 표시
        body.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
        srDetailModal.show();

        // 수정 버튼에 SR ID 연결 (상세 창에서 바로 수정 창으로 이동)
        editBtn.onclick = function() {
            srDetailModal.hide();
            openSrModal(srId);
        };

        try {
            const res = await fetch(`/sr/ajax/${srId}`);
            const json = await res.json();

            if (json.ok) {
                const d = json.data;
                const severityBadge = d.severity === 'High' ? '<span class="badge bg-danger">High</span>' :
                                      d.severity === 'Middle' ? '<span class="badge bg-warning text-dark">Middle</span>' :
                                      '<span class="badge bg-secondary">Low</span>';

                const resultBadge = d.result === '완료' ? '<span class="badge bg-success">완료</span>' :
                                    '<span class="badge bg-secondary">미완료</span>';

                body.innerHTML = `
                    <div class="row g-3">
                        <div class="col-md-6 border-end">
                            <div class="mb-3">
                                <label class="small text-muted fw-bold">고객사</label>
                                <div class="fs-5 fw-bold text-dark">${d.company}</div>
                                <div class="small text-muted">${d.location}</div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-6">
                                    <label class="small text-muted fw-bold">중요도</label>
                                    <div>${severityBadge}</div>
                                </div>
                                <div class="col-6">
                                    <label class="small text-muted fw-bold">상태</label>
                                    <div>${resultBadge}</div>
                                </div>
                            </div>
                            <div class="mb-3">
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
                                <div class="small">
                                    <span class="fw-bold">처리자:</span> ${d.handler || '-'} <br>
                                    <span class="fw-bold">처리일:</span> ${d.handled_date || '-'}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                body.innerHTML = '<div class="text-center text-danger py-4">정보를 불러오지 못했습니다.</div>';
            }
        } catch (e) {
            console.error(e);
            body.innerHTML = '<div class="text-center text-danger py-4">통신 오류가 발생했습니다.</div>';
        }
    }

    // [2] 등록/수정 모달 열기
    async function openSrModal(srId = null) {
        document.getElementById('srForm').reset();

        if (srId) {
            document.getElementById('srModalTitle').innerText = 'SR 수정';
            document.getElementById('edit_sr_id').value = srId;

            try {
                const res = await fetch(`/sr/ajax/${srId}`);
                const json = await res.json();
                if(json.ok) {
                    const d = json.data;
                    document.getElementById('edit_location').value = d.location;
                    document.getElementById('edit_company').value = d.company;
                    document.getElementById('edit_category').value = d.category || '요청';
                    document.getElementById('edit_severity').value = d.severity || 'Low';
                    document.getElementById('edit_requester').value = d.requester || '';
                    document.getElementById('edit_request_date').value = d.request_date;
                    document.getElementById('edit_content').value = d.content;
                    document.getElementById('edit_handler').value = d.handler || '';
                    document.getElementById('edit_handled_date').value = d.handled_date || '';
                    document.getElementById('edit_result').value = d.result || '미완료';
                }
            } catch(e) {
                alert('데이터 로드 실패');
                return;
            }
        } else {
            document.getElementById('srModalTitle').innerText = 'SR 등록';
            document.getElementById('edit_sr_id').value = '';
            document.getElementById('edit_request_date').value = new Date().toISOString().split('T')[0];
            document.getElementById('edit_category').value = '요청';
            document.getElementById('edit_severity').value = 'Low';
            document.getElementById('edit_result').value = '미완료';
        }

        srModal.show();
    }

    // [3] 저장
    async function saveSr() {
        const form = document.getElementById('srForm');
        if(!form.checkValidity()) { form.reportValidity(); return; }

        const formData = new FormData(form);
        const srId = document.getElementById('edit_sr_id').value;
        const url = srId ? `/sr/ajax/${srId}/update` : `/sr/ajax/create`;

        try {
            const res = await fetch(url, { method: 'POST', body: formData });
            const json = await res.json();

            if(json.ok) {
                await Swal.fire('저장 완료', '정상적으로 처리되었습니다.', 'success');
                window.location.reload();
            } else {
                Swal.fire('오류', json.message || '저장 중 문제가 발생했습니다.', 'error');
            }
        } catch(e) {
            Swal.fire('오류', '서버 통신 오류', 'error');
        }
    }

    // [4] 삭제
    async function deleteSr(srId) {
        const result = await Swal.fire({
            title: '삭제하시겠습니까?',
            text: "삭제된 데이터는 복구할 수 없습니다.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: '삭제',
            cancelButtonText: '취소'
        });

        if(result.isConfirmed) {
            try {
                const res = await fetch(`/sr/ajax/${srId}/delete`, { method: 'POST' });
                const json = await res.json();
                if(json.ok) {
                    await Swal.fire('삭제됨', '삭제되었습니다.', 'success');
                    window.location.reload();
                } else {
                    Swal.fire('오류', json.message, 'error');
                }
            } catch(e) {
                Swal.fire('오류', '통신 오류', 'error');
            }
        }
    }