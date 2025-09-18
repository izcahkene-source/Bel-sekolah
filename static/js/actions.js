document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ actions.js jalan...");

  let deleteId = null;

  // ========================
  // 🔹 Tambah Jadwal
  // ========================
  window.openAddModal = function () {
    fetch("/add_form").then(r => r.text()).then(html => {
      document.getElementById("addFormContainer").innerHTML = html;
      new bootstrap.Modal(document.getElementById("addModal")).show();

      document.getElementById("addForm").onsubmit = e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        fetch("/add", { method: "POST", body: fd })
          .then(r => r.json()).then(s => {
            if (s.success) {
              addRowToTable(s);
              bootstrap.Modal.getInstance(document.getElementById("addModal")).hide();
            }
          });
      };
    });
  };

  function addRowToTable(s) {
    let table = document.querySelector(`table[data-day="${s.day}"] tbody`);
    if (!table) location.reload(); 
    else table.insertAdjacentHTML("beforeend", rowHTML(s));
  }

  function rowHTML(s) {
    return `
    <tr id="row-${s.id}">
      <td>${s.time}</td>
      <td>${s.label}</td>
      <td>${s.sound}</td>
      <td>
        <audio id="audio-${s.id}">
          <source src="/static/sounds/${s.sound}" type="audio/mpeg">
        </audio>
        <button id="btn-${s.id}" class="btn btn-success btn-sm" onclick="toggleSound(${s.id})">▶️</button>
        <button class="btn btn-warning btn-sm" onclick="openEditModal(${s.id}, '${s.day}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="openDeleteModal(${s.id}, '${s.label}')">🗑️</button>
      </td>
    </tr>`;
  }

  // ========================
  // 🔹 Edit
  // ========================
  window.openEditModal = function (id, day) {
    fetch(`/edit/${id}`).then(r => r.text()).then(html => {
      document.getElementById("editFormContainer").innerHTML = html;
      document.getElementById("editDay").textContent = day;
      new bootstrap.Modal(document.getElementById("editModal")).show();
    });
  };

  window.submitEditForm = function (id) {
    const fd = new FormData(document.getElementById("editForm"));
    fetch(`/edit/${id}`, { method: "POST", body: fd })
      .then(r => r.json()).then(s => {
        if (s.success) {
          updateRowInTable(s);
          bootstrap.Modal.getInstance(document.getElementById("editModal")).hide();
        }
      });
  };

  function updateRowInTable(s) {
    document.querySelector(`#row-${s.id}`).outerHTML = rowHTML(s);
  }



  // ========================
  // 🔹 Preview Suara
  // ========================
  window.previewSound = function (selectId, audioId, btnId, uploadId) {
    const select = document.getElementById(selectId);
    const upload = document.getElementById(uploadId);
    const audio = document.getElementById(audioId);
    const btn = document.getElementById(btnId);

    audio.src = upload.files[0] ? URL.createObjectURL(upload.files[0]) : "/static/sounds/" + select.value;

    if (audio.paused) {
      audio.play(); btn.textContent = "⏹ Stop";
    } else {
      audio.pause(); audio.currentTime = 0; btn.textContent = "▶️ Coba";
    }
  };

  // ========================
  // 🔹 Toggle Play
  // ========================
  window.toggleSound = function (id) {
    const audio = document.getElementById(`audio-${id}`);
    const btn = document.getElementById(`btn-${id}`);

    document.querySelectorAll("audio").forEach(a => {
      if (a !== audio) { a.pause(); a.currentTime = 0; }
    });
    document.querySelectorAll("button[id^='btn-']").forEach(b => b.textContent = "▶️");

    if (audio.paused) {
      audio.play().then(() => btn.textContent = "⏸️").catch(err => {
        console.error("Gagal play:", err);
        alert("⚠️ Browser blokir autoplay. Klik tombol lagi.");
      });
    } else {
      audio.pause(); audio.currentTime = 0; btn.textContent = "▶️";
    }
  };
});



// ========================
// 🔹 Hapus
// ========================
window.openDeleteModal = function (id, label) {
  deleteId = id;
  document.getElementById("deleteLabel").textContent = label;
  new bootstrap.Modal(document.getElementById("deleteModal")).show();
};

document.getElementById("confirmDeleteBtn").onclick = () => {
  if (!deleteId) return;
  fetch(`/delete/${deleteId}`, { method: "POST" })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        // 🔹 Tutup modal konfirmasi dulu
        const deleteModalEl = document.getElementById("deleteModal");
        bootstrap.Modal.getInstance(deleteModalEl).hide();

        // 🔹 Setelah modal konfirmasi benar-benar tertutup
        deleteModalEl.addEventListener("hidden.bs.modal", () => {
          // Baru tampilkan modal sukses
          const successModal = new bootstrap.Modal(document.getElementById("successModal"));
          document.getElementById("successModalBody").innerHTML = "✅ Jadwal berhasil dihapus!";
          successModal.show();

          // Reload setelah modal sukses ditutup
          document.getElementById("successModal").addEventListener("hidden.bs.modal", () => {
            location.reload();
          }, { once: true });
        }, { once: true });
      }
    });
};
// ========================
// 🔹 Reset
// ========================
window.openResetModal = function () {
  new bootstrap.Modal(document.getElementById("resetModal")).show();
};

document.addEventListener("DOMContentLoaded", function () {
  const confirmBtn = document.getElementById("confirmResetBtn");

  if (confirmBtn) {
    confirmBtn.addEventListener("click", function () {
      fetch("/reset", { method: "POST" })
        .then(r => r.json())
        .then(res => {
          console.log("Respon server:", res); // 🔍 cek di console
          if (res.success) {
            // Tutup modal konfirmasi
            bootstrap.Modal.getInstance(document.getElementById("resetModal")).hide();

            // Buka modal sukses
            document.getElementById("successModalBody").innerHTML = "♻️ Jadwal berhasil direset ke default!";
            new bootstrap.Modal(document.getElementById("successModal")).show();
            

            // Reload setelah modal sukses ditutup
            document.getElementById("successModal").addEventListener("hidden.bs.modal", function () {
              location.reload();
            }, { once: true });
          }
        })
        .catch(err => console.error("Error fetch reset:", err));
    });
  }
});
