//-----------USERNAME VALIDATION--------//
$(document).ready(function () {
  $("#username_create").on("input", function () {
    var input = $(this);
    var is_name = input.val();
    var errorMessageContainer = $(".username-error-message");

    if (is_name.length === 0) {
      input.removeClass("valid invalid");
      errorMessageContainer.text("").removeClass("error-message");
    } else if (/\s/.test(is_name)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Username cannot contain spaces")
        .addClass("error-message");
    } else if (is_name.length < 4 || is_name.length > 25) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Username must be between 4 and 25 characters")
        .addClass("error-message");
    } else if ((is_name.match(/[^a-zA-Z0-9]/g) || []).length > 2) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Username can contain a maximum of 2 special characters (including hyphens and underscores)")
        .addClass("error-message");
    } else {
      $.post("/check_username", { username: is_name.toLowerCase() }, function (data) {
        if (data.username_exists) {
          input.removeClass("valid").addClass("invalid");
          errorMessageContainer
            .text("Username is already taken")
            .addClass("error-message");
        } else {
          input.removeClass("invalid").addClass("valid");
          errorMessageContainer.text("").removeClass("error-message");
        }
      });
    }
  });
});

//-----------EMAIL VALIDATION--------//
$(document).ready(function () {
  $("#email_create").on("input", function () {
    var input = $(this);
    var email = input.val();
    var errorMessageContainer = $(".email-error-message");

    var emailPattern = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
    var invalidDomainPattern = /\.(c0m|c00m)$/i;
    var testEmailPattern = /@test/i;

    if (email.length === 0) {
      input.removeClass("valid invalid");
      errorMessageContainer.text("").removeClass("error-message");
    } else if (/\s/.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email cannot contain spaces")
        .addClass("error-message");
    } else if (testEmailPattern.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email cannot contain @test")
        .addClass("error-message");
    } else if (invalidDomainPattern.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Invalid email format. Please use .com instead of .c0m")
        .addClass("error-message");
    } else if (emailPattern.test(email)) {
      $.post("/check_email", { email: email }, function (data) {
        if (data.email_exists) {
          input.removeClass("valid").addClass("invalid");
          errorMessageContainer
            .text("Email is already registered")
            .addClass("error-message");
        } else {
          input.removeClass("invalid").addClass("valid");
          errorMessageContainer.text("").removeClass("error-message");
        }
      });
    } else {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Invalid email format")
        .addClass("error-message");
    }
  });
});

//-----------PASSWORD VALIDATION--------//
$(document).ready(function () {
  $("#pwd_create").on("input", function () {
    var input = $(this);
    var password = input.val();
    var errorMessageContainer = $(".password-error-message");

    if (password.length === 0) {
      input.removeClass("valid invalid");
      errorMessageContainer.text("").removeClass("error-message");
    } else if (!validatePassword(password)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .html(
        "<ul class='error-message'>" +
        "<li>Password must contain at least one uppercase letter (A-Z)</li>" +
        "<li>Password must contain at least one lowercase letter (a-z)</li>" +
        "<li>Password must contain at least one number (0-9)</li>" +
        "<li>Password must contain at least one special character (@, $, !, %, *, ?, &)</li>" +
        "<li>Password must be at least 6 characters long</li>" +
        "</ul>"
      )
        .addClass("error-message");
    } else {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer.text("").removeClass("error-message");
    }
  });
});

//-----------CONFIRM PASSWORD VALIDATION--------//
$(document).ready(function () {
  $("#confirm_pwd_create").on("input", function () {
    var input = $(this);
    var confirmPassword = input.val();
    var password = $("#pwd_create").val();
    var errorMessageContainer = $(".confirm-password-error-message");

    if (confirmPassword.length === 0) {
      input.removeClass("valid invalid");
      errorMessageContainer.text("").removeClass("error-message");
    } else if (!validateConfirmPassword(password, confirmPassword)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Confirm password must match the password")
        .addClass("error-message");
    } else {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer.text("").removeClass("error-message");
    }
  });
});

//CHECK FORMS IF ALL VALID AND NO ERROR MESSAGES
function checkFormValidity() {
  var usernameIsValid = $("#username_create").hasClass("valid") && !$(".username-error-message").hasClass("error-message");
  var emailIsValid = $("#email_create").hasClass("valid") && !$(".email-error-message").hasClass("error-message");
  var passwordIsValid = $("#pwd_create").hasClass("valid") && !$(".password-error-message").hasClass("error-message");
  var confirmPasswordIsValid = $("#confirm_pwd_create").hasClass("valid") && !$(".confirm-password-error-message").hasClass("error-message");
  var languageIsSelected = isLanguageSelected();

  return usernameIsValid && emailIsValid && passwordIsValid && confirmPasswordIsValid && languageIsSelected;
}

$(document).ready(function () {
  $("#username_create, #email_create, #pwd_create, #confirm_pwd_create, #language-select").on("input change", function () {
    if (checkFormValidity()) {
      $("#signup-button").prop("disabled", false);
    } else {
      $("#signup-button").prop("disabled", true);
    }
  });
});

