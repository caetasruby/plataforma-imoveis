// Hook simples para carregar dados da API com estados de carregamento e erro
import { useCallback, useEffect, useState } from "react";

export default function usarDados(funcao, dependencias = []) {
  const [dados, setDados] = useState(null);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState(null);

  const carregar = useCallback(() => {
    let cancelado = false;
    setACarregar(true);
    setErro(null);
    funcao()
      .then((d) => !cancelado && setDados(d))
      .catch((e) => !cancelado && setErro(e))
      .finally(() => !cancelado && setACarregar(false));
    return () => { cancelado = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencias);

  useEffect(() => carregar(), [carregar]);
  return { dados, setDados, aCarregar, erro, recarregar: carregar };
}
