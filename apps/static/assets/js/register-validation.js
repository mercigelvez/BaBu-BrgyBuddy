$(document).ready(function () {
  $("#username_create").on("input", function () {
    var input = $(this);
    var is_name = input.val();
    var errorMessageContainer = $(".username-error-message");

    if (is_name.length >= 4 && is_name.length <= 25) {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer.text("").removeClass("error-message");

      // Check if the username is available
      $.ajax({
        url: '{{ url_for("authentication_blueprint.register") }}',
        type: "POST",
        data: { username: is_name },
        success: function (response) {
          if (response.includes("Username already taken")) {
            errorMessageContainer
              .text("Username is already taken")
              .removeClass("success-message")
              .addClass("error-message");
          } else {
            errorMessageContainer
              .text("Username is available")
              .removeClass("error-message")
              .addClass("success-message");
          }
        },
        error: function (error) {
          console.log(error);
        },
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

$(document).ready(function () {
    $("#email_create").on("input", function () {
      var input = $(this);
      var email = input.val();
      var errorMessageContainer = $(".email-error-message");
  
      // Regular expression pattern for email validation
      var emailPattern = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
  
      // Check for .c0m or .c00m instead of .com
      var invalidDomainPattern = /\.(c0m|c00m)$/i;
  
      // Check if the email is in the proper format and doesn't contain .c0m or .c00m
      if (emailPattern.test(email) && !invalidDomainPattern.test(email)) {
        input.removeClass("invalid").addClass("valid");
        errorMessageContainer.text("Valid email format").addClass("success-message").removeClass("error-message");
  
        // Check if the email already exists
        $.ajax({
          url: '{{ url_for("authentication_blueprint.check_email_availability") }}',
          type: "POST",
          data: { email: email },
          success: function (response) {
            if (response.available) {
              errorMessageContainer.text("Email is available").addClass("success-message").removeClass("error-message");
            } else {
              input.removeClass("valid").addClass("invalid");
              errorMessageContainer.text("Email is already registered").removeClass("success-message").addClass("error-message");
            }
          },
          error: function (error) {
            console.log(error);
          },
        });
      } else if (invalidDomainPattern.test(email)) {
        input.removeClass("valid").addClass("invalid");
        errorMessageContainer.text("Invalid email format. Please use .com instead of .c0m or .c00m").addClass("error-message").removeClass("success-message");
      } else {
        input.removeClass("valid").addClass("invalid");
        errorMessageContainer.text("Invalid email format").addClass("error-message").removeClass("success-message");
      }
    });
  });