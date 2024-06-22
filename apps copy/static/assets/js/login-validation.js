$(document).ready(function() {
    $('#toggle-password').click(function() {
        $(this).toggleClass('fa-eye fa-eye-slash');
        let input = $('#password-input');
        if (input.attr('type') == 'password') {
            input.attr('type', 'text');
        } else {
            input.attr('type', 'password');
        }
    });
});