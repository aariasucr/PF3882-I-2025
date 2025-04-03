package com.pf3882.ejemplo;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;


@OpenAPIDefinition(
  info = @Info(
    title = "Ejemplo API",
    version = "1.0",
    description = "Ejemplo de una API REST con Spring Boot y Swagger"
  )
)

@SpringBootApplication(scanBasePackages = "com.pf3882.ejemplo")
public class EjemploApplication {

	public static void main(String[] args) {
		SpringApplication.run(EjemploApplication.class, args);
	}

  @Bean
  public RestTemplate restTemplate() {
    // esto es lo que se usa para conectarse a otras APIs
    return new RestTemplate();
  }

}
