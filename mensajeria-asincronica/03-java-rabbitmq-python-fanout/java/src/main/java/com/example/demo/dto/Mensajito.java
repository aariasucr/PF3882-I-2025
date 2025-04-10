package com.example.demo.dto;

import lombok.*;

import java.io.Serializable;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@ToString
public class Mensajito implements Serializable {
    private int id;
    private String titulo;
    private String descripcion;
}
