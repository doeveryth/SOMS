async function postForm(url, formEl) {
  const formData = new FormData(formEl);
  const res = await fetch(url, { method: "POST", body: formData });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.ok) {
    const msg = data && data.message ? data.message : "요청 처리에 실패했습니다.";
    throw new Error(msg);
  }
  return data;
}

function setText(el, text) {
  if (!el) return;
  el.textContent = text || "";
}

function todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function setDateIfEmpty(formEl, inputName) {
  const el = formEl ? formEl.querySelector(`[name=${inputName}]`) : null;
  if (!el) return;
  if (!el.value) el.value = todayISO();
}

const ALLOWED_EXT = [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".csv", ".xlsx", ".xls", ".docx", ".pptx", ".zip"];
const MAX_UPLOAD_MB = 500;

function isAllowedFile(name) {
  const lower = name.toLowerCase();
  return ALLOWED_EXT.some((ext) => lower.endsWith(ext));
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return "-";
  const sizes = ["B", "KB", "MB", "GB"];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < sizes.length - 1) {
    val /= 1024;
    i += 1;
  }
  return `${val.toFixed(val < 10 && i > 0 ? 1 : 0)} ${sizes[i]}`;
}

async function loadWorkAttachments(workId) {
  const el = document.getElementById("workDetailAttachments");
  if (!el) return;

  el.textContent = "첨부파일을 불러오는 중...";
  try {
    const res = await fetch(`/work/ajax/${workId}/attachments`);
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error();

    if (!data.items || data.items.length === 0) {
      el.textContent = "첨부파일이 없습니다.";
      return;
    }

    const list = document.createElement("ul");
    list.className = "list-group list-group-flush";

    data.items.forEach((a) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center gap-2";

      const link = document.createElement("a");
      link.href = a.download_url;
      link.textContent = a.name || "-";
      link.className = "text-decoration-none";

      const right = document.createElement("div");
      right.className = "d-flex align-items-center gap-2";

      const size = document.createElement("span");
      size.className = "text-muted small";
      size.textContent = formatBytes(a.size);

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-sm btn-outline-danger";
      delBtn.textContent = "삭제";
      delBtn.addEventListener("click", async () => {
        if (!confirm("첨부파일을 삭제하시겠습니까?")) return;
        const res = await fetch(`/work/ajax/attachments/${a.id}/delete`, { method: "POST" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.ok) {
          alert(data.message || "삭제에 실패했습니다.");
          return;
        }
        loadWorkAttachments(workId);
      });

      right.appendChild(size);
      right.appendChild(delBtn);

      li.appendChild(link);
      li.appendChild(right);
      list.appendChild(li);
    });

    el.innerHTML = "";
    el.appendChild(list);
  } catch (e) {
    el.textContent = "첨부파일을 불러오지 못했습니다.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const createModalEl = document.getElementById("workCreateModal");
  const createForm = document.getElementById("workCreateForm");
  const createError = document.getElementById("workCreateError");

  if (createModalEl && createForm) {
    createModalEl.addEventListener("show.bs.modal", () => {
      createForm.reset();
      setText(createError, "");
      setDateIfEmpty(createForm, "work_date");
    });

    createForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      setText(createError, "");

      const fileInput = createForm.querySelector("input[type=file]");
      if (fileInput && fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (!isAllowedFile(file.name)) {
          setText(createError, `허용되지 않은 확장자입니다. (${ALLOWED_EXT.join(", ")})`);
          return;
        }
        if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
          setText(createError, `파일 크기는 ${MAX_UPLOAD_MB}MB 이하만 가능합니다.`);
          return;
        }
      }

      try {
        await postForm("/work/ajax/create", createForm);
        window.location.reload();
      } catch (err) {
        setText(createError, err.message);
      }
    });
  }

  const editModalEl = document.getElementById("workEditModal");
  const editForm = document.getElementById("workEditForm");
  const editError = document.getElementById("workEditError");

  if (editModalEl && editForm) {
    editModalEl.addEventListener("show.bs.modal", (event) => {
      const btn = event.relatedTarget;
      setText(editError, "");

      const workId = btn.getAttribute("data-work-id");
      editForm.setAttribute("data-work-id", workId);

      editForm.querySelector("[name=person_id]").value = btn.getAttribute("data-person-id") || "";
      editForm.querySelector("[name=work_date]").value = btn.getAttribute("data-work-date") || "";
      editForm.querySelector("[name=work_type]").value = btn.getAttribute("data-type") || "";
      editForm.querySelector("[name=summary]").value = btn.getAttribute("data-summary") || "";
      editForm.querySelector("[name=description]").value = btn.getAttribute("data-description") || "";

      setDateIfEmpty(editForm, "work_date");
    });

    editForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      setText(editError, "");
      const workId = editForm.getAttribute("data-work-id");
      try {
        await postForm(`/work/ajax/${workId}/update`, editForm);
        window.location.reload();
      } catch (err) {
        setText(editError, err.message);
      }
    });
  }

  const delModalEl = document.getElementById("workDeleteModal");
  const delForm = document.getElementById("workDeleteForm");
  const delError = document.getElementById("workDeleteError");
  const delLabel = document.getElementById("workDeleteLabel");

  if (delModalEl && delForm) {
    delModalEl.addEventListener("show.bs.modal", (event) => {
      const btn = event.relatedTarget;
      setText(delError, "");

      const workId = btn.getAttribute("data-work-id");
      const label = btn.getAttribute("data-label") || `ID ${workId}`;

      delForm.setAttribute("data-work-id", workId);
      setText(delLabel, label);
    });

    delForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      setText(delError, "");
      const workId = delForm.getAttribute("data-work-id");
      try {
        await postForm(`/work/ajax/${workId}/delete`, delForm);
        window.location.reload();
      } catch (err) {
        setText(delError, err.message);
      }
    });
  }

  const workRows = document.querySelectorAll(".work-row");
  if (workRows.length > 0) {
    workRows.forEach((row) => {
      row.addEventListener("click", () => {
        const workId = row.dataset.workId;

        document.getElementById("workDetailId").textContent = workId || "-";
        document.getElementById("workDetailCompany").textContent = row.dataset.company || "-";
        document.getElementById("workDetailLastName").textContent = row.dataset.lastName || "-";
        document.getElementById("workDetailDate").textContent = row.dataset.workDate || "-";
        document.getElementById("workDetailType").textContent = row.dataset.type || "-";
        document.getElementById("workDetailSummary").textContent = row.dataset.summary || "-";
        document.getElementById("workDetailContent").textContent = row.dataset.description || "-";
        document.getElementById("workDetailSubmitter").textContent = row.dataset.submitter || "-";
        document.getElementById("workDetailCreateDate").textContent = row.dataset.createDate || "-";
        document.getElementById("workDetailHistory").textContent = row.dataset.history || "-";
        document.getElementById("workDetailEtc").textContent = row.dataset.etc || "-";

        loadWorkAttachments(workId);
      });
    });
  }

  const workFilterText = document.getElementById("workFilterText");
  const workFilterFrom = document.getElementById("workFilterFrom");
  const workFilterTo = document.getElementById("workFilterTo");

  function applyWorkFilter() {
    const rows = document.querySelectorAll("#tab-work tbody tr");
    const keyword = (workFilterText?.value || "").toLowerCase();
    const from = workFilterFrom?.value || "";
    const to = workFilterTo?.value || "";

    rows.forEach((row) => {
      const date = row.dataset.workDate || "";
      const summary = row.dataset.summary || "";
      const desc = row.dataset.description || "";
      const submitter = row.dataset.submitter || "";
      const text = `${summary} ${desc} ${submitter}`.toLowerCase();

      const matchText = !keyword || text.includes(keyword);
      const matchFrom = !from || (date && date >= from);
      const matchTo = !to || (date && date <= to);

      row.style.display = matchText && matchFrom && matchTo ? "" : "none";
    });
  }

  if (workFilterText) workFilterText.addEventListener("input", applyWorkFilter);
  if (workFilterFrom) workFilterFrom.addEventListener("change", applyWorkFilter);
  if (workFilterTo) workFilterTo.addEventListener("change", applyWorkFilter);

  const hash = window.location.hash;
  if (hash && hash.startsWith("#tab-")) {
    const trigger = document.querySelector(`[data-bs-target="${hash}"]`);
    if (trigger) {
      const tab = new bootstrap.Tab(trigger);
      tab.show();
    }
  }
  function initializeSelect2() {
  // 계층 2 (Type)
  if ($('#type').length) {
    $('#type').select2({
      theme: 'bootstrap-5',
      placeholder: '-- 검색하여 선택 --',
      allowClear: false,
      width: '100%',
      dropdownParent: $('#assetAddModal')
    });
  }

  // 계층 3 (Item)
  if ($('#item').length) {
    $('#item').select2({
      theme: 'bootstrap-5',
      placeholder: '-- 검색하여 선택 (선택사항) --',
      allowClear: true,
      width: '100%',
      dropdownParent: $('#assetAddModal'),
      language: {
        noResults: function() {
          return "검색 결과가 없습니다";
        },
        searching: function() {
          return "검색 중...";
        }
      }
    });
  }

  // 유지보수업체
  if ($('#maintenance_company').length) {
    $('#maintenance_company').select2({
      theme: 'bootstrap-5',
      placeholder: '-- 검색하여 선택 --',
      allowClear: false,
      width: '100%',
      dropdownParent: $('#assetAddModal')
    });
  }

  // 공급자명
  if ($('#supplier').length) {
    $('#supplier').select2({
      theme: 'bootstrap-5',
      placeholder: '-- 검색하여 선택 (선택사항) --',
      allowClear: true,
      width: '100%',
      dropdownParent: $('#assetAddModal')
    });
  }
}

  // 모달이 열릴 때 Select2 초기화
const assetAddModal = document.getElementById('assetAddModal');
  if (assetAddModal) {
    assetAddModal.addEventListener('shown.bs.modal', function () {
      // 기존 Select2 인스턴스 제거
      if ($('#type').hasClass('select2-hidden-accessible')) {
        $('#type').select2('destroy');
      }
      if ($('#item').hasClass('select2-hidden-accessible')) {
        $('#item').select2('destroy');
      }
      if ($('#maintenance_company').hasClass('select2-hidden-accessible')) {
        $('#maintenance_company').select2('destroy');
      }
      if ($('#supplier').hasClass('select2-hidden-accessible')) {
        $('#supplier').select2('destroy');
      }

      // 새로 초기화
      initializeSelect2();
    });

    // 모달이 닫힐 때 Select2 초기화
    assetAddModal.addEventListener('hidden.bs.modal', function () {
      if ($('#type').length) $('#type').val('').trigger('change');
      if ($('#item').length) $('#item').val(null).trigger('change');
      if ($('#maintenance_company').length) $('#maintenance_company').val('12').trigger('change');
      if ($('#supplier').length) $('#supplier').val(null).trigger('change');
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const workCalendarItems = document.querySelectorAll(".work-calendar-item");
  if (workCalendarItems.length > 0) {
    workCalendarItems.forEach((item) => {
      item.addEventListener("click", () => {
        const workId = item.dataset.workId;

        document.getElementById("workDetailId").textContent = workId || "-";
        document.getElementById("workDetailCompany").textContent = item.dataset.company || "-";
        document.getElementById("workDetailLastName").textContent = item.dataset.lastName || "-";
        document.getElementById("workDetailDate").textContent = item.dataset.workDate || "-";
        document.getElementById("workDetailType").textContent = item.dataset.type || "-";
        document.getElementById("workDetailSummary").textContent = item.dataset.summary || "-";
        document.getElementById("workDetailContent").textContent = item.dataset.description || "-";
        document.getElementById("workDetailSubmitter").textContent = item.dataset.submitter || "-";
        document.getElementById("workDetailHistory").textContent = item.dataset.history || "-";
        document.getElementById("workDetailEtc").textContent = item.dataset.etc || "-";

        const modal = new bootstrap.Modal(document.getElementById("workDetailModal"));
        modal.show();
      });
    });
  }
});
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

// 서버 수정 모달 열기
async function editServer(serverId, personId) {
  const modal = new bootstrap.Modal(document.getElementById('serverEditModal'));
  const form = document.getElementById('serverEditForm');
  const body = document.getElementById('serverEditBody');

  try {
    const res = await fetch(`/customers/${personId}/servers/${serverId}/edit`);
    const data = await res.json();

    if (!data.ok) {
      alert(data.message || '로드에 실패했습니다.');
      return;
    }

    const d = data.data;
    body.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">서버명</label>
          <input type="text" class="form-control" name="chServerName" value="${d.chServerName || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">서버정보</label>
          <input type="text" class="form-control" name="chServerInfo" value="${d.chServerInfo || ''}">
        </div>
      </div>
    `;

    form.action = `/customers/${personId}/servers/${serverId}/edit`;
    modal.show();
  } catch (err) {
    alert('로드에 실패했습니다.');
  }
}

// 담당자 수정 모달 열기
async function editContact(contactId, personId) {
  const modal = new bootstrap.Modal(document.getElementById('contactEditModal'));
  const form = document.getElementById('contactEditForm');
  const body = document.getElementById('contactEditBody');

  try {
    const res = await fetch(`/customers/${personId}/contacts/${contactId}/edit`);
    const data = await res.json();

    if (!data.ok) {
      alert(data.message || '로드에 실패했습니다.');
      return;
    }

    const d = data.data;
    body.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">역할</label>
          <input type="text" class="form-control" name="role_type" value="${d.role_type || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">이름</label>
          <input type="text" class="form-control" name="name" value="${d.name || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">전화</label>
          <input type="text" class="form-control" name="phone" value="${d.phone || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">이메일</label>
          <input type="email" class="form-control" name="email" value="${d.email || ''}">
        </div>
      </div>
    `;

    form.action = `/customers/${personId}/contacts/${contactId}/edit`;
    modal.show();
  } catch (err) {
    alert('로드에 실패했습니다.');
  }
}

// 계약 수정 모달 열기
async function editContract(contractId, personId) {
  const modal = new bootstrap.Modal(document.getElementById('contractEditModal'));
  const form = document.getElementById('contractEditForm');
  const body = document.getElementById('contractEditBody');

  try {
    const res = await fetch(`/customers/${personId}/contracts/${contractId}/edit`);
    const data = await res.json();

    if (!data.ok) {
      alert(data.message || '로드에 실패했습니다.');
      return;
    }

    const d = data.data;
    body.innerHTML = `
      <div class="row g-3">
        <div class="col-12">
          <label class="form-label">계약명</label>
          <input type="text" class="form-control" name="contract_name" value="${d.contract_name || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">금액</label>
          <input type="text" class="form-control" name="contract_amount" value="${d.contract_amount || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">통화</label>
          <input type="text" class="form-control" name="currency" value="${d.currency || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">계약시작일</label>
          <input type="date" class="form-control" name="contract_start_date" value="${d.contract_start_date || ''}">
        </div>
        <div class="col-md-6">
          <label class="form-label">계약종료일</label>
          <input type="date" class="form-control" name="contract_end_date" value="${d.contract_end_date || ''}">
        </div>
        <div class="col-12">
          <label class="form-label">비고</label>
          <textarea class="form-control" name="contract_notes" rows="3">${d.contract_notes || ''}</textarea>
        </div>
      </div>
    `;

    form.action = `/customers/${personId}/contracts/${contractId}/edit`;
    modal.show();
  } catch (err) {
    alert('로드에 실패했습니다.');
  }
}

// 삭제 함수들
function deleteAsset(assetId, personId) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  fetch(`/customers/${personId}/ci/${assetId}/delete`, { method: 'POST' })
    .then(() => location.reload());
}

function deleteServer(serverId, personId) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  fetch(`/customers/${personId}/servers/${serverId}/delete`, { method: 'POST' })
    .then(() => location.reload());
}

function deleteContact(contactId, personId) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  fetch(`/customers/${personId}/contacts/${contactId}/delete`, { method: 'POST' })
    .then(() => location.reload());
}

function deleteContract(contractId, personId) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  fetch(`/customers/${personId}/contracts/${contractId}/delete`, { method: 'POST' })
    .then(() => location.reload());
}