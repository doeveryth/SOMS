$(document).ready(function () {
    // 페이지 로드 시 계약 목록 불러오기
    loadContracts();
});

// 1. 계약 목록 불러오기
async function loadContracts() {
    // [중요] 함수 실행 시점에 ID를 가져와야 안전함
    const personIdInput = document.getElementById('pagePersonId');
    if (!personIdInput) {
        console.error("HTML에 'pagePersonId' input 태그가 없습니다.");
        return;
    }
    const personId = personIdInput.value;

    try {
        const res = await fetch(`/contract/ajax/${personId}`);
        const json = await res.json();
        const tbody = document.getElementById('contractListBody');

        if (!tbody) return;
        tbody.innerHTML = '';

        if (!json.data || json.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-5 text-muted">등록된 계약 정보가 없습니다.</td></tr>';
            return;
        }

        // [테이블 렌더링] 부분의 첫 번째 <td> 수정
        json.data.forEach(c => {
            let statusBadge = c.status == '1' ? '<span class="badge bg-success">사용중</span>' :
                c.status == '2' ? '<span class="badge bg-info text-dark">개통중</span>' :
                    c.status == '5' ? '<span class="badge bg-secondary">해지</span>' :
                        '<span class="badge bg-warning text-dark">기타</span>';

            tbody.innerHTML += `
        <tr>
            <td class="text-center">${statusBadge}</td>
            <td class="fw-bold text-dark">${c.service_type || '-'}</td>
            <td class="text-primary fw-bold">${c.service_number || '-'}</td>
            <td>${c.open_date}</td>
            <td>${c.terminate_date}</td>
            <td>${c.amount || '-'}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-danger" onclick="deleteContract(${c.id})" title="삭제">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
        });
    } catch (e) {
        console.error("Load Error:", e);
        const tbody = document.getElementById('contractListBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">데이터 로드 중 오류가 발생했습니다.</td></tr>';
    }
}

// 2. 모달 열기 (폼 초기화)
function openContractModal() {
    const form = document.getElementById('contractForm');
    if (form) form.reset();

    const modalEl = document.getElementById('contractModal');
    if (modalEl) new bootstrap.Modal(modalEl).show();
}

// 3. 계약 저장 (Create)
async function saveContract() {
    const form = document.getElementById('contractForm');
    const formData = new FormData(form);

    try {
        const res = await fetch('/contract/ajax/create', {method: 'POST', body: formData});
        const json = await res.json();

        if (json.ok) {
            // 모달 닫기
            const modalEl = document.getElementById('contractModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();

            // 목록 새로고침 및 알림
            loadContracts();
            Swal.fire({
                icon: 'success',
                title: '저장 완료',
                text: '계약 정보가 등록되었습니다.',
                timer: 1500,
                showConfirmButton: false
            });
        } else {
            Swal.fire('오류', json.message, 'error');
        }
    } catch (e) {
        console.error("Save Error:", e);
        Swal.fire('통신 오류', '서버와 통신 중 문제가 발생했습니다.', 'error');
    }
}

// 4. 계약 삭제 (Delete)
async function deleteContract(id) {
    if (!confirm('정말 이 계약 정보를 삭제하시겠습니까?')) return;

    try {
        const res = await fetch(`/contract/ajax/${id}/delete`, {method: 'POST'});
        if (res.ok) {
            loadContracts();
            Swal.fire({
                icon: 'success',
                title: '삭제됨',
                text: '계약 정보가 삭제되었습니다.',
                timer: 1500,
                showConfirmButton: false
            });
        } else {
            Swal.fire('오류', '삭제에 실패했습니다.', 'error');
        }
    } catch (e) {
        console.error("Delete Error:", e);
        Swal.fire('통신 오류', '서버와 통신 중 문제가 발생했습니다.', 'error');
    }
}