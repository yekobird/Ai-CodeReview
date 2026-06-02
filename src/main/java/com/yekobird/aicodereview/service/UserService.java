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

}
