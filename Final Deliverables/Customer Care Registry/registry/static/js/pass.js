// Function to make the password visible in password type inputs 
// Common to login form, sign up form, change password form 
function showPassword(){
    var x = document.getElementById("password-input");
    x.type = x.type == "password" ? "text" : "password";

    var x = document.getElementById("password-input1");
    x.type = x.type == "password" ? "text" : "password";

    var x = document.getElementById("password-input2");
    x.type = x.type == "password" ? "text" : "password";
}

