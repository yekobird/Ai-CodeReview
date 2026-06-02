package com.yekobird.aicodereview.service;

import java.sql.Connection;
import java.sql.Statement;
import java.io.File;
import java.io.FileReader;

/**
 * 用户服务（故意写了很多问题用来测试审查）
 */
public class UserService {

    private Connection connection;

    // 问题1: 硬编码密码
    private String dbPassword = "admin123456";

    public UserService() {
        // 问题2: 类名应该是大驼峰，这里故意写错
    }

    // 问题3: SQL注入
    public void getUserById(String userId) {
        String sql = "SELECT * FROM users WHERE id = " + userId;
        try {
            Statement stmt = connection.createStatement();
            stmt.execute(sql);
            // 问题4: 异常吞没
        } catch (Exception e) {
        }
    }

    // 问题5: 资源未关闭 + 路径遍历
    public String readFiles(String fileName) {
        try {
            FileReader reader = new FileReader(new File("/home/data/" + fileName));
            char[] buffer = new char[1024];
            reader.read(buffer);
            return new String(buffer);
        } catch (Exception e) {
            // 问题6: 宽泛异常捕获
            return null;
        }
    }

    // 问题7: 循环内字符串拼接
    public String buildUserList(int count) {
        String result = "";
        for (int i = 0; i < count; i++) {
            result += "User" + i + ",";
        }
        return result;
    }

    // 问题8: 魔法数字
    public String getLevel(int score) {
        if (score > 90) {
            return "A";
        } else if (score > 60) {
            return "B";
        }
        return "C";
    }

    public void createUser(String name, String email) {
        System.out.println("创建用户");
    }

    // 问题10: 循环内创建对象
    public void processItems(int n) {
        for (int i = 0; i < n; i++) {
            StringBuilder sb = new StringBuilder();
            sb.append("处理第").append(i).append("个");
            System.out.println(sb.toString());
        }
    }
}
