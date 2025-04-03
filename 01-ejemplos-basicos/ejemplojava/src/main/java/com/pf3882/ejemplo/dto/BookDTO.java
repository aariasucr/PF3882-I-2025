package com.pf3882.ejemplo.dto;

import lombok.*;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@ToString
public class BookDTO {
  private int id;
  private String title;
  private String author;
}
