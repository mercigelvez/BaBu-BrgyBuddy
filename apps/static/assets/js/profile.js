$(document).ready(function () {
  $('#editProfileBtn').click(function () {
    $('#usernameInput, #emailInput, #currentPasswordInput, #newPasswordInput, #saveChangesBtn').removeAttr('disabled')
    $('#saveChangesBtn').show() // Show the "Save Changes" button
    $(this).hide() // Hide the "Edit" button

    // Add event listeners for real-time validation
    $('#profileForm input').on('input', function () {
      validateInput(this)
    })

    // Add event listener for username validation
    $('#usernameInput').on('input', validateUsername)

    // Add event listener for email validation
    $('#emailInput').on('input', validateEmail)

    // Add event listener for current password validation
    $('#currentPasswordInput').on('input', validateCurrentPassword)

    // Add event listener for new password validation
    $('#newPasswordInput').on('input', validateNewPassword)
  })

  $('#saveChangesBtn').click(function (e) {
    e.preventDefault() // Prevent the form from submitting

    // Check if all required fields are valid
    let isValid = true
    $('#profileForm input[required]').each(function () {
      if (!this.checkValidity()) {
        isValid = false
        $(this).addClass('is-invalid')
      } else {
        $(this).removeClass('is-invalid')
      }
    })

    // If all fields are valid, submit the form
    if (isValid) {
      $('#profileForm').submit()
    }
  })

  // Reset form validation when the modal is closed
  $('#profileModal').on('hidden.bs.modal', function () {
    const currentUsername = '{{ current_user.username }}'.toLowerCase()
    const newUsername = $('#usernameInput').val().toLowerCase()

    // Reset validation for all input fields except the username
    $('#profileForm input').not('#usernameInput').removeClass('is-invalid')

    // Reset username validation only if the new username matches the current username
    if (newUsername === currentUsername) {
      $('#usernameInput').removeClass('is-invalid')
      $('.username-error-message').text('')
    }
  })
})

function validateInput(input) {
  if (input.checkValidity()) {
    $(input).removeClass('is-invalid')
  } else {
    $(input).addClass('is-invalid')
  }
}

function validateUsername() {
  const newUsername = $('#usernameInput').val().toLowerCase()
  const currentUsername = '{{ current_user.username }}'.toLowerCase()
  const errorMessageContainer = $('#usernameInput').siblings('.invalid-feedback')

  // If the new username is the same as the current username, skip the check
  if (newUsername === currentUsername) {
    $('#usernameInput').removeClass('is-invalid')
    errorMessageContainer.text('')
    return
  }

  // Check if username contains space
  if (/\s/.test(newUsername)) {
    $('#usernameInput').addClass('is-invalid')
    errorMessageContainer
      .text('Username cannot contain spaces')
      .addClass('error-message')
  } else if (newUsername.length >= 4 && newUsername.length <= 25) {
    // Convert username to lowercase before sending AJAX request
    $.post('/check_username', { username: newUsername }, function (data) {
      if (data.username_exists) {
        $('#usernameInput').addClass('is-invalid')
        errorMessageContainer
          .text('Username is already taken')
          .addClass('error-message')
      } else {
        $('#usernameInput').removeClass('is-invalid').addClass('valid')
        errorMessageContainer.text('')
      }
    })
  } else {
    $('#usernameInput').addClass('is-invalid')
    if (newUsername.length === 0) {
      errorMessageContainer
        .text('Username is required')
        .addClass('error-message')
    } else {
      errorMessageContainer
        .text('Username must be between 4 and 25 characters')
        .addClass('error-message')
    }
  }
}

function validateCurrentPassword() {
  const currentPassword = $('#currentPasswordInput').val()
  const currentPasswordErrorMessage = $('#currentPasswordInput').siblings('.invalid-feedback')

  if (currentPassword.length === 0) {
    $('#currentPasswordInput').addClass('is-invalid')
    currentPasswordErrorMessage.text('Please enter your current password.')
  } else {
    $('#currentPasswordInput').removeClass('is-invalid')
    currentPasswordErrorMessage.text('')
  }
}

function validateNewPassword() {
  const newPassword = $('#newPasswordInput').val()
  const newPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/
  const newPasswordErrorMessage = $('#newPasswordInput').siblings('.invalid-feedback')

  if (!newPasswordRegex.test(newPassword)) {
    $('#newPasswordInput').addClass('is-invalid')
    newPasswordErrorMessage.text('Password must be at least 6 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character.')
  } else {
    $('#newPasswordInput').removeClass('is-invalid')
    newPasswordErrorMessage.text('')
  }
}
