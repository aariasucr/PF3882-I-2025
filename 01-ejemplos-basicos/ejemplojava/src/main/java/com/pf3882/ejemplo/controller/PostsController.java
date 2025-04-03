package com.pf3882.ejemplo.controller;

import com.pf3882.ejemplo.dto.PostDTO;
import com.pf3882.ejemplo.service.PostService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/posts")
@Tag(name = "Posts", description = "cosas de posts")
public class PostsController {
  private final PostService postService;

  public PostsController(PostService postService) {
    this.postService = postService;
  }

  @GetMapping("/{id}")
  public PostDTO getPost(@PathVariable("id") int id) {
    return this.postService.getPost(id);
  }
}
