function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

var imageCodeId = "";

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    imageCodeId=generateUUID();
    var url="/api/v1.0/image_codes/"+imageCodeId;
    $(".image-code img").attr("src",url)
}

function sendSMSCode() {
    // 点击发送验证码后执行
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }
    $.get("/api/v1.0/sms_codes/"+mobile, {image_code:imageCode, image_code_id:imageCodeId},
        function(data){
            if ("0" != data.errno) {
                $("#image-code-err span").html(data.errmsg); 
                $("#image-code-err").show();
                if ("4002" == data.errno || "4004" == data.errno) {
                    generateImageCode();
                }
                $(".phonecode-a").attr("onclick", "sendSMSCode();");
            } else {
                var $time = $(".phonecode-a");
                var duration = 60;
                var intervalid = setInterval(function(){
                    $time.html(duration + "秒"); 
                    if(duration === 1){
                        clearInterval(intervalid);
                        $time.html('获取验证码'); 
                        $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    }
                    duration = duration - 1;
                }, 1000, 60); 
            }
    });
}

$(document).ready(function() {
    generateImageCode();
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });
    $(".form-register").submit(function(e){
        e.preventDefault();

        mobile = $("#mobile").val();
        phoneCode = $("#phonecode").val();
        passwd = $("#password").val();
        passwd2 = $("#password2").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        //　发送注册请求
        var req_data={
            "mobile":mobile,
            "sms_code":phoneCode,
            "password":passwd,
            "password2":passwd2
        };

        var req_json=JSON.stringify(req_data);  //转换为json字符串后发送
        $.ajax({
            headers:{
                // 添加请求头字段X-CSRFToken，保存csrf_token值，方便CSRFProtect进行验证
                "X-CSRFToken":getCookie("csrf_token")
            },
            url:"/api/v1.0/users",
            type:"post",
            data:req_json,
            contentType: "application/json;charset=utf-8",
            success:function (resp) {
                if (resp.errno=="0"){
                    //注册成功
                    location.href="/index.html";
                }else{
                    //注册失败
                    // alert(resp.errmsg);
                    $("#password2-err").html(resp.errmsg);
                    $("#password2-err").show()
                }
            }
        })

    });
})