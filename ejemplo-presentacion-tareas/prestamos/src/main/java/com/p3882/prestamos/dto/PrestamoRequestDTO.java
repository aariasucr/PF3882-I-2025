package com.p3882.prestamos.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PrestamoRequestDTO {
  private int usuarioId;
  private int libroId;
  private int diasPrestamo;
}
