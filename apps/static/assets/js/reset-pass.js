function validatePassword(password) {
  var passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/;
  return passwordPattern.test(password);
}

function validateConfirmPassword(password, confirmPassword) {
  return password === confirmPassword;
}

function updateSubmitButtonState() {
  var password = $("#new_pass").val();
  var confirmPassword = $("#confirm_new_pass").val();
  var isPasswordValid = validatePassword(password);
  var isConfirmPasswordValid = validateConfirmPassword(password, confirmPassword);
  
  $("#submit-btn").prop("disabled", !(isPasswordValid && isConfirmPasswordValid));
}

$(document).ready(function () {
  $("#new_pass, #confirm_new_pass").on("input", function () {
      updateSubmitButtonState();
  });

  $("#new_pass").on("input", function () {
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
      
      updateSubmitButtonState();
  });

  $("#confirm_new_pass").on("input", function () {
      var input = $(this);
      var confirmPassword = input.val();
      var password = $("#new_pass").val();
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
      
      updateSubmitButtonState();
  });

  // Initially disable the submit button
  $("#submit-btn").prop("disabled", true);
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