package com.example.demo.controller;

import com.example.demo.dto.Mensajito;
import com.google.gson.Gson;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/rabbitmq")
@Tag(name = "RabbitMQ", description = "rabbit")
public class RabbitMQController {
    private final RabbitTemplate rabbitTemplate;

    public RabbitMQController(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    @GetMapping
    public String send() {
        Mensajito mensajito = new Mensajito();
        mensajito.setId(1);
        mensajito.setDescripcion("blah blah");
        mensajito.setTitulo("un titulito");

        // mandamos un mensaje arbitrario a la cola
//        rabbitTemplate.convertAndSend("cola-de-libros", "soy un mensaje desde java");

        // mandamos un objeto de Java a la cola (esto mata a python)
//        rabbitTemplate.convertAndSend("cola-de-libros", mensajito);

        // mandamos un objeeto toString()
//        rabbitTemplate.convertAndSend("cola-de-libros", mensajito.toString());

        // mandamos un json a la cola
        Gson gson = new Gson();
        rabbitTemplate.convertAndSend("cola-de-libros", gson.toJson(mensajito));

//        String x ="{\"id\":1,\"titulo\":\"un titulito\",\"descripcion\":\"blah blah\"}";
//        Mensajito m = gson.fromJson(x, Mensajito.class);

        return "mensaje enviado";
    }
}
