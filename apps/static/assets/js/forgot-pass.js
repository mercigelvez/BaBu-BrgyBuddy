//-----------EMAIL VALIDATION--------//
$(document).ready(function () {
    $("#email").on("input", function () {
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
          if (data.exists) {
            input.removeClass("invalid").addClass("valid");
            errorMessageContainer
              .text("Email exists")
              .addClass("success-message")
              .removeClass("error-message");
          } else {
            input.removeClass("valid").addClass("invalid");
            errorMessageContainer
              .text("Email does not exist")
              .addClass("error-message")
              .removeClass("success-message");
          }
        });
      } else if (invalidDomainPattern.test(email)) {
        input.removeClass("valid").addClass("invalid");
        errorMessageContainer
          .text("Invalid email format. Please use .com instead of .c0m or .c00m")
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
  