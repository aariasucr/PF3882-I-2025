package com.pf3882.ejemplo.dto;

import lombok.*;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@ToString
public class PostDTO {
  private int userId;
  private int id;
  private String title;
  private String body;
}
