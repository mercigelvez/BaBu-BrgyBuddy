//-----------EMAIL VALIDATION--------//
$(document).ready(function () {
  $("#email").on("input", function () {
    var input = $(this);
    var email = input.val();
    var errorMessageContainer = $(".email-error-message");
    // Regular expression pattern for email validation
    var emailPattern = /^\[\\w-\\.\]+@(\[\\w-\]+\\.)+\[\\w-\]{2,4}$/;
    // Check for .c0m or .c00m instead of .com
    var invalidDomainPattern = /\\.(c0m|c00m)$/i;
    // Check if email contains @test
    var testEmailPattern = /@test/i;

    // Check if email contains space
    if (/\\s/.test(email)) {
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
    } else if (invalidDomainPattern.test(email)) {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Invalid email format. Please use .com instead of .c0m")
        .addClass("error-message")
        .removeClass("success-message");
    } else if (emailPattern.test(email)) {
      input.removeClass("invalid").addClass("valid");
      errorMessageContainer
        .text("Valid email address")
        .removeClass("error-message")
        .addClass("success-message");
    } else if (email === "") {
      input.removeClass("valid").addClass("invalid");
      errorMessageContainer
        .text("Email is required")
        .addClass("error-message")
        .removeClass("success-message");
    }
  });
});