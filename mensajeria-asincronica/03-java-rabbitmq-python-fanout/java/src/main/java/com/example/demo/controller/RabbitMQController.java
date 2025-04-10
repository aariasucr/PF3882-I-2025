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

        Gson gson = new Gson();

        // el routingKey es ignorado cuando el exchange es de tipo fanout
        rabbitTemplate.convertAndSend("exchange1", "patito", gson.toJson(mensajito));

        // si quisiera mandarl eun mensaje a un topic especifico
//        rabbitTemplate.convertAndSend("topic1", gson.toJson(mensajito));

        return "mensaje enviado";
    }
}
