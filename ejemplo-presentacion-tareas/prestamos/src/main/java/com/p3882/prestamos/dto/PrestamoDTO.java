package com.p3882.prestamos.dto;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Date;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PrestamoDTO {
  private int id;
  private String nombre;
  private String apellidos;
  private String email;
  private String tituloLibro;
  private String autorLibro;
  @JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")
  private Date fechaCreacionPrestamo;
  @JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")
  private Date fechaVencimientoPrestamo;
}

