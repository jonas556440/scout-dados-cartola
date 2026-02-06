import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log para console em desenvolvimento
    console.error('ErrorBoundary capturou erro:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-lg bg-destructive/10 mb-4">
                <AlertCircle className="w-8 h-8 text-destructive" />
              </div>
              <h1 className="text-2xl font-bold text-foreground mb-2">Oops! Algo deu errado</h1>
              <p className="text-muted-foreground text-sm">
                Desculpe pelo incômodo. Estamos cientes do problema e trabalhando para resolvê-lo.
              </p>
            </div>

            {/* Detalhes do erro em desenvolvimento */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-muted p-4 rounded-lg mb-6 max-h-40 overflow-auto">
                <p className="text-xs font-mono text-muted-foreground">
                  {this.state.error.message}
                </p>
              </div>
            )}

            {/* Ações */}
            <div className="space-y-3">
              <Button 
                onClick={this.handleReset}
                className="w-full gap-2 bg-primary hover:bg-primary/90"
              >
                <RefreshCw className="w-4 h-4" />
                Tentar Novamente
              </Button>
              
              <Button 
                variant="outline"
                className="w-full gap-2"
                asChild
              >
                <Link to="/">
                  <Home className="w-4 h-4" />
                  Voltar para Home
                </Link>
              </Button>
            </div>

            {/* Dica de suporte */}
            <div className="mt-8 p-4 bg-muted/30 rounded-lg border border-muted">
              <p className="text-xs text-muted-foreground text-center">
                Se o problema persistir, tente limpar o cache do navegador ou contate{' '}
                <a 
                  href="mailto:contato@scoutdados.com.br"
                  className="text-primary hover:underline"
                >
                  contato@scoutdados.com.br
                </a>
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
