//-----------USERNAME VALIDATION--------//
$(document).ready(function () {
  $("#username_create").on("input", function () {
    var input = $(this);
    var is_name = input.val();
    var errorMessageContainer = $(".username-error-message");

    // Check if username contains space
    if (/\s/.test(is_name)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Username cannot contain spaces")
        .addClass("error-message")
        .removeClass("success-message");
    } else if (is_name.length >= 4 && is_name.length <= 25) {
      // Convert username to lowercase before sending AJAX request
      $.post("/check_username", { username: is_name.toLowerCase() }, function (data) {
        if (data.username_exists) {
          input.removeClass("valid").addClass("invalid");
          errorMessageContainer
            .text("Username is already taken")
            .addClass("error-message")
            .removeClass("success-message");
        } else {
          input.removeClass("invalid").addClass("valid");
          errorMessageContainer
            .text("Username is valid")
            .addClass("success-message")
            .removeClass("error-message");
        }
      });
    } else {
      input.removeClass("valid").addClass("invalid");
      if (is_name.length === 0) {
        errorMessageContainer
          .text("Username is required")
          .addClass("error-message")
          .removeClass("success-message");
      } else {
        errorMessageContainer
          .text("Username must be between 4 and 25 characters")
          .addClass("error-message")
          .removeClass("success-message");
      }
    }
  });
});


//-----------EMAIL VALIDATION--------//
$(document).ready(function () {
  $("#email_create").on("input", function () {
    var input = $(this);
    var email = input.val();
    var errorMessageContainer = $(".email-error-message");

    // Regular expression pattern for email validation
    var emailPattern = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;

    // Check for .c0m or .c00m instead of .com
    var invalidDomainPattern = /\.(c0m|c00m)$/i;

    // Check if email contains @test
    var testEmailPattern = /@test/i;

    // Check if email contains space
    if (/\s/.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email cannot contain spaces")
        .addClass("error-message")
        .removeClass("success-message");
    } else if (testEmailPattern.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email cannot contain @test")
        .addClass("error-message")
        .removeClass("success-message");
    } else if (emailPattern.test(email) && !invalidDomainPattern.test(email)) {
      // Send AJAX request to check if email exists
      $.post("/check_email", { email: email }, function (data) {
        if (data.email_exists) {
          input.removeClass("valid").addClass("invalid");
          errorMessageContainer
            .text("Email is already registered")
            .addClass("error-message")
            .removeClass("success-message");
        } else {
          input.removeClass("invalid").addClass("valid");
          errorMessageContainer
            .text("Valid email format")
            .addClass("success-message")
            .removeClass("error-message");
        }
      });
    } else if (invalidDomainPattern.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Invalid email format. Please use .com instead of .c0m")
        .addClass("error-message")
        .removeClass("success-message");
    } else {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email is required")
        .addClass("error-message")
        .removeClass("success-message");
    }
  });
});


//-----------PASSWORD VALIDATION--------//

function validatePassword(password) {
  // At least one uppercase letter, one lowercase letter, one number, one special character, and minimum 6 characters in length
  var passwordPattern =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/;
  return passwordPattern.test(password);
}

$(document).ready(function () {
  $("#pwd_create").on("input", function () {
    var input = $(this);
    var password = input.val();
    var errorMessageContainer = $(".password-error-message");

  if (validatePassword(password)) {
    input.removeClass("invalid").addClass("valid");
    errorMessageContainer
      .text("Valid Password")
      .addClass("success-message")
      .removeClass("error-message");
  } else {
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
      .addClass("error-message")
      .removeClass("success-message");
  }
  });
});

function togglePasswordVisibility(inputId, iconId) {
  var passwordInput = document.getElementById(inputId);
  var eyeIcon = document.getElementById(iconId);
  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    eyeIcon.classList.remove("fa-eye-slash");
    eyeIcon.classList.add("fa-eye");
  } else {
    passwordInput.type = "password";
    eyeIcon.classList.remove("fa-eye");
    eyeIcon.classList.add("fa-eye-slash");
  }
}

//-----------CONFIRM PASSWORD VALIDATION--------//

function validateConfirmPassword(password, confirmPassword) {
  return password === confirmPassword;
}

$(document).ready(function () {
  $("#confirm_pwd_create").on("input", function () {
    var input = $(this);
    var confirmPassword = input.val();
    var password = $("#pwd_create").val();
    var errorMessageContainer = $(".confirm-password-error-message");

    if (validateConfirmPassword(password, confirmPassword)) {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer
        .text("Passwords match")
        .addClass("success-message")
        .removeClass("error-message");
    } else {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Confirm password must match the password")
        .addClass("error-message")
        .removeClass("success-message");
    }
  });
});

//CHECK FORMS IF ALL VALID
function checkFormValidity() {
  var usernameIsValid = $("#username_create").hasClass("valid");
  var emailIsValid = $("#email_create").hasClass("valid");
  var passwordIsValid = $("#pwd_create").hasClass("valid");
  var confirmPasswordIsValid = $("#confirm_pwd_create").hasClass("valid");

  return usernameIsValid && emailIsValid && passwordIsValid && confirmPasswordIsValid;
}

$(document).ready(function () {

  $("#username_create, #email_create, #pwd_create, #confirm_pwd_create").on("input", function () {
    if (checkFormValidity()) {
      $("#signup-button").prop("disabled", false);
    } else {
      $("#signup-button").prop("disabled", true);
    }
  });
});

