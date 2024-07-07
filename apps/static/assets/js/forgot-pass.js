$(document).ready(function () {
  $("#email").on("input", function () {
    var input = $(this);
    var email = input.val().toLowerCase();
    var errorMessageContainer = $(".email-error-message");
    var submitButton = $("#submit-btn");

    // Regular expression pattern for email validation
    var emailPattern = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;

    // Check for .c0m or .c00m instead of .com
    var invalidDomainPattern = /\.(c0m|c00m|cm)$/i;

    // Check if email contains @test
    var testEmailPattern = /@test/i;

    if (email.trim() === "") {
      setInvalid();
    } else if (/\s/.test(email)) {
      setInvalid("Email cannot contain spaces");
    } else if (testEmailPattern.test(email)) {
      setInvalid("Email cannot contain @test");
    } else if (invalidDomainPattern.test(email)) {
      setInvalid("Invalid email format. Please use correct format of domain");
    } else if (!emailPattern.test(email)) {
      setInvalid("Invalid email format");
    } else {
      setValid();
    }

    function setInvalid(message) {
      input.removeClass("valid").addClass("invalid");
      if (message) {
        errorMessageContainer
          .text(message)
          .addClass("error-message")
          .removeClass("success-message");
      } else {
        errorMessageContainer.text("").removeClass("error-message success-message");
      }
      submitButton.prop('disabled', true);
    }

    function setValid() {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer.text("").removeClass("error-message success-message");
      submitButton.prop('disabled', false);
    }
  });
});