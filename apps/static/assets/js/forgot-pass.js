//-----------EMAIL VALIDATION--------//
$(document).ready(function () {
  $("#email").on("submit", function (event) {
    event.preventDefault(); // Prevent the form from being submitted normally
    var email = $("#email").val();
    $.post("/forgot_password", { email: email }, function (data) {
      $(".email-error-message")
        .text("If an account with that email address exists, we’ve sent a password reset link.")
        .addClass("success-message");
    });
  });
});

  