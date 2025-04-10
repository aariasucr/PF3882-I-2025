package com.pf3882.rabbitmq.receptorjava.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class RabbitMQConsumer {

    @RabbitListener(queues = "cola-de-libros")
    public void consumeMessage(String message) {
        log.info("Mensajre recibido: {}", message);
        // Process the message here
    }
}
