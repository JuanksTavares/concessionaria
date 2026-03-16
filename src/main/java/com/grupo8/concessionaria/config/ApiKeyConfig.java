package com.grupo8.concessionaria.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ApiKeyConfig {

    @Value("${auth.api-key}")
    private String apiKey;

    public String getApiKey() {
        return apiKey;
    }
}
