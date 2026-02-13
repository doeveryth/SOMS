    // [해결 2] 외부 JS 충돌 방지용 더미 함수
    window.initializeSelect2 = function() {};

    // [해결 1] 함수명 일치 (openUserRegisterModal)
    // 이 함수는 $(document).ready 안에 두지 말고 밖에 둬야 HTML에서 찾을 수 있습니다.
    function openUserRegisterModal() {
        document.getElementById('userModalTitle').innerHTML = '<i class="bi bi-person-plus-fill me-2"></i>사용자 등록';

        const form = document.querySelector('#userModal form');
        if(form) form.reset();

        const idInput = document.getElementById('modal_user_id');
        idInput.readOnly = false;
        idInput.classList.remove('bg-light');

        // [UI 개선] 등록 시 안내 문구
        document.getElementById('modal_password').placeholder = "비워두면 초기비번(new1234!)으로 설정됨";

        document.getElementById('modal_target_id').value = '';
        document.getElementById('id_help_text').innerText = "로그인에 사용할 ID입니다.";

        new bootstrap.Modal(document.getElementById('userModal')).show();
    }

    // [해결 1] 함수명 일치 (openUserEditModal)
    function openUserEditModal(btn) {
        const d = btn.dataset;

        document.getElementById('userModalTitle').innerHTML = '<i class="bi bi-pencil-square me-2"></i>사용자 수정';

        const idInput = document.getElementById('modal_user_id');
        idInput.value = d.id;
        idInput.readOnly = true;
        idInput.classList.add('bg-light');

        // [UI 개선] 수정 시 안내 문구
        document.getElementById('modal_password').placeholder = "변경시에만 입력하세요";

        document.getElementById('modal_target_id').value = d.id;
        document.getElementById('id_help_text').innerText = "아이디는 수정할 수 없습니다.";

        document.getElementById('modal_user_name').value = d.name;
        document.getElementById('modal_department').value = d.dept === 'None' ? '' : d.dept;
        document.getElementById('modal_email').value = d.email === 'None' ? '' : d.email;
        document.getElementById('modal_role').value = d.role;
        document.getElementById('modal_password').value = '';

        new bootstrap.Modal(document.getElementById('userModal')).show();
    }
