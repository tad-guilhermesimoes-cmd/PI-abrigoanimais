CREATE TABLE `animais` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(80) NOT NULL,
  `especie` enum('CAO','GATO') NOT NULL,
  `raca` varchar(80) NOT NULL DEFAULT 'SRD',
  `sexo` enum('MACHO','FEMEA') NOT NULL,
  `porte` enum('PEQUENO','MEDIO','GRANDE') NOT NULL,
  `data_nascimento` date DEFAULT NULL,
  `cor` varchar(60) DEFAULT NULL,
  `comportamento` text,
  `vacinado` tinyint(1) NOT NULL DEFAULT '0',
  `vacinas_detalhes` text,
  `castrado` tinyint(1) NOT NULL DEFAULT '0',
  `necessidades_especiais` text,
  `descricao` text,
  `status` enum('DISPONIVEL','EM_PROCESSO','ADOTADO') NOT NULL DEFAULT 'DISPONIVEL',
  `cliques_interesse` int NOT NULL DEFAULT '0',
  `criado_em` datetime NOT NULL DEFAULT (now()),
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_animais_status` (`status`),
  KEY `ix_animais_especie` (`especie`),
  KEY `ix_animais_vacinado` (`vacinado`),
  KEY `ix_animais_porte` (`porte`),
  KEY `ix_animais_castrado` (`castrado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `configuracoes` (
  `chave` varchar(50) NOT NULL,
  `valor` text NOT NULL,
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`chave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `fotos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `animal_id` int NOT NULL,
  `arquivo` varchar(255) NOT NULL,
  `miniatura` varchar(255) NOT NULL,
  `ordem` int NOT NULL DEFAULT '0',
  `criado_em` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_fotos_animal_id` (`animal_id`),
  CONSTRAINT `fotos_ibfk_1` FOREIGN KEY (`animal_id`) REFERENCES `animais` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `historico_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `animal_id` int NOT NULL,
  `status_anterior` enum('DISPONIVEL','EM_PROCESSO','ADOTADO') DEFAULT NULL,
  `status_novo` enum('DISPONIVEL','EM_PROCESSO','ADOTADO') NOT NULL,
  `usuario_id` int DEFAULT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `ix_historico_status_animal_id` (`animal_id`),
  CONSTRAINT `historico_status_ibfk_1` FOREIGN KEY (`animal_id`) REFERENCES `animais` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historico_status_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `sessoes` (
  `token_hash` varchar(64) NOT NULL,
  `usuario_id` int NOT NULL,
  `criado_em` datetime NOT NULL DEFAULT (now()),
  `expira_em` datetime NOT NULL,
  `ip` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`token_hash`),
  KEY `ix_sessoes_usuario_id` (`usuario_id`),
  KEY `ix_sessoes_expira_em` (`expira_em`),
  CONSTRAINT `sessoes_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `tentativas_login` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(150) NOT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `sucesso` tinyint(1) NOT NULL,
  `criado_em` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_tentativas_login_criado_em` (`criado_em`),
  KEY `ix_tentativas_login_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `senha_hash` varchar(100) NOT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT '1',
  `criado_em` datetime NOT NULL DEFAULT (now()),
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
