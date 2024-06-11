function is_username(asValue) {
  var regExp = /^(?=.*[a-zA-Z])[-a-zA-Z0-9_.]{2,20}$/;
  return regExp.test(asValue);
}

function sign_up() {
  let username = $("#username").val();
  let nama_lengkap = $("#nama_lengkap").val();
  let password = $("#password").val();
  let password2 = $("#confirmpassword").val();

  if (username === "") {
      $("#username").addClass("is-invalid");
      $("#help_username1")
          .text("Tolong Masukkan Username Anda")
      $("#username").focus();
      return;
  }
  else {
      $("#username").removeClass("is-invalid");
  }

  if (!is_username(username)) {
      $("#username").addClass("is-invalid");
      $("#help_username1").text("Mohon cek username Anda. Gunakan 2-10 karakter bahasa Inggris, angka, atau karakter khusus (._-)")
      $("#username").focus();
      return;
  }



  if (nama_lengkap === "") {
      $("#nama_lengkap").addClass("is-invalid");
      $("#nama_lengkap").focus();
      return;
  }
  else {
      $("#nama_lengkap").removeClass("is-invalid");
  }

  if (password === "") {
      $("#password").addClass("is-invalid");
      $("#password").focus();
      return;
  }
  else {
      $("#password").removeClass("is-invalid");
  }


  if (password2 === "") {
      $("#confirmpassword").addClass("is-invalid");
      $("#help_pw2")
          .text("Tolong Masukkan Konfirmasi Password")
      $("#confirmpassword").focus();
      return;
  } else if (password2 !== password) {
      $("#confirmpassword").addClass("is-invalid");
      $("#help_pw2")
          .text("Konfirmasi Password Tidak Sesuai")
      $("#confirmpassword").focus();
      return;
  }
  else {
      $("#confirmpassword").removeClass("is-invalid");
  }


  $.ajax({
      type: "POST",
      url: "/user_signup",
      data: {
          username: username,
          nama_lengkap: nama_lengkap,
          password: password,
      },
      success: function (response) {
          if (response["result"] === "success") {
              Swal.fire({
                  title: 'Pendaftaran Member Berhasil',
                  text: 'Silahkan login.',
                  icon: 'Sukses',
                  button: 'ok',
              })
              window.location.href = "/login";
          } else {
              $("#username").addClass("is-invalid");
              $("#help_username1")
                  .text("Username sudah terdaftar")
          }
      },
  });
}

function sign_in() {
    let username = $("#username").val();
    let password = $("#password").val();

    if (username === "") {
        $("#username").addClass("is-invalid");
        $("#help_username1").text("Tolong Masukkan Username Anda");
        $("#username").focus();
        return;
    } else {
        $("#username").removeClass("is-invalid");
    }

    if (password === "") {
        $("#password").addClass("is-invalid");
        $("#password").focus();
        return;
    } else {
        $("#password").removeClass("is-invalid");
    }

    $.ajax({
        type: "POST",
        url: "/sign_in",
        data: {
            username_give: username,
            password_give: password,
        },
        success: function (response) {
            if (response["result"] === "success") {
                let expires = new Date();
                expires.setTime(expires.getTime() + (60 * 60 * 1000)); // 60 minutes
                $.cookie("mytoken", response["token"], { path: "/", expires: expires });

                Swal.fire({
                    title: 'Berhasil',
                    text: 'Selamat Datang.',
                    icon: 'success',
                    confirmButtonText: 'Ok'
                }).then(() => {
                    if (response["role"] === "admin") {
                        window.location.replace("/admin_panel");
                    } else {
                        window.location.replace("/");
                    }
                });
            } else {
                alert(response["msg"]);
            }
        },
    });
}


function registerbtn() {
  $("#boxnama").toggleClass("d-none")
  $("#sign-in-btn").toggleClass("d-none")
  $("#sign-up-box").toggleClass("d-none")
  $("#sign-up-btn").toggleClass("d-none")
  $("#create1").toggleClass("d-none")
  $("#create2").toggleClass("d-none")
}

function bersih() {
  $("#username").val('');
  $("#nama_lengkap").val('');
  $("#password").val('');
  $("#confirmpassword").val('');
}