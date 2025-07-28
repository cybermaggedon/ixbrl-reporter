"""
Unit tests for ixbrl_reporter.__main__ module
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

from ixbrl_reporter.__main__ import main


class TestMainArgumentParsing:
    """Test main() function argument parsing"""
    
    def test_insufficient_args_exits_with_usage(self):
        """main() with insufficient args should print usage and exit"""
        test_cases = [
            [],  # No args
            ["script"],  # Just script name
            ["script", "config"],  # Missing report and format
            ["script", "config", "report"]  # Missing format
        ]
        
        for args in test_cases:
            with patch('sys.argv', args):
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    stderr_output = mock_stderr.getvalue()
                    assert "Usage:" in stderr_output
                    assert "ixbrl-reporter <config> <report> <format>" in stderr_output
    
    def test_sufficient_args_proceeds(self):
        """main() with sufficient args should proceed to processing"""
        with patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html']):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                    with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            # Set up mocks to avoid deep execution
                            mock_config.load.return_value = Mock()
                            mock_accounts.get_class.return_value = Mock()
                            mock_data_source.return_value = Mock()
                            
                            # Should not raise SystemExit for insufficient args
                            try:
                                main()
                            except Exception:
                                # Other exceptions are fine, we just want to test arg parsing
                                pass


class TestMainVersionRetrieval:
    """Test version retrieval from package metadata"""
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_version_from_package_metadata_success(self):
        """Version should be retrieved from package metadata when available"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                    with patch('ixbrl_reporter.__main__.version', return_value='1.2.3') as mock_version:
                        
                        # Set up mocks
                        config_instance = Mock()
                        mock_config.load.return_value = config_instance
                        mock_accounts.get_class.return_value = Mock()
                        mock_data_source.return_value = Mock()
                        
                        try:
                            main()
                        except Exception:
                            pass  # We only care about version retrieval
                        
                        # Verify version was called and set
                        mock_version.assert_called_once_with("ixbrl-reporter")
                        config_instance.set.assert_any_call("internal.software-version", "1.2.3")
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_version_fallback_on_exception(self):
        """Version should fallback to 'unknown' when package metadata fails"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                    with patch('ixbrl_reporter.__main__.version', side_effect=Exception("Package not found")) as mock_version:
                        
                        # Set up mocks
                        config_instance = Mock()
                        mock_config.load.return_value = config_instance
                        mock_accounts.get_class.return_value = Mock()
                        mock_data_source.return_value = Mock()
                        
                        try:
                            main()
                        except Exception:
                            pass  # We only care about version retrieval
                        
                        # Verify version was attempted and fallback was used
                        mock_version.assert_called_once_with("ixbrl-reporter")
                        config_instance.set.assert_any_call("internal.software-version", "unknown")


class TestMainConfigurationLoading:
    """Test configuration loading and processing"""
    
    @patch('sys.argv', ['script', 'test-config.yaml', 'report.yaml', 'html'])
    def test_config_loading(self):
        """Config should be loaded from specified file"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                    with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                        
                        # Set up mocks
                        config_instance = Mock()
                        mock_config.load.return_value = config_instance
                        mock_accounts.get_class.return_value = Mock()
                        mock_data_source.return_value = Mock()
                        
                        try:
                            main()
                        except Exception:
                            pass  # We only care about config loading
                        
                        # Verify config was loaded with correct file
                        mock_config.load.assert_called_once_with('test-config.yaml')
                        
                        # Verify software name and version were set
                        config_instance.set.assert_any_call("internal.software-name", "ixbrl-reporter")
                        config_instance.set.assert_any_call("internal.software-version", "1.1.2")
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_accounts_processing(self):
        """Accounts should be processed from config"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                    with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                        
                        # Set up mocks
                        config_instance = Mock()
                        config_instance.get.side_effect = lambda key: {
                            "accounts.kind": "csv",
                            "accounts.file": "test.csv"
                        }[key]
                        mock_config.load.return_value = config_instance
                        
                        accounts_class = Mock()
                        accounts_session = Mock()
                        accounts_class.return_value = accounts_session
                        mock_accounts.get_class.return_value = accounts_class
                        
                        mock_data_source.return_value = Mock()
                        
                        try:
                            main()
                        except Exception:
                            pass  # We only care about accounts processing
                        
                        # Verify accounts were processed correctly
                        config_instance.get.assert_any_call("accounts.kind")
                        config_instance.get.assert_any_call("accounts.file")
                        mock_accounts.get_class.assert_called_once_with("csv")
                        accounts_class.assert_called_once_with("test.csv")
                        mock_data_source.assert_called_once_with(config_instance, accounts_session)


class TestMainOutputFormats:
    """Test different output format handling"""
    
    def setup_method(self):
        """Set up common mocks for output format tests"""
        self.mock_config = Mock()
        self.mock_config.get.side_effect = lambda key: {
            "accounts.kind": "csv",
            "accounts.file": "test.csv",
            "report.taxonomy": "test-taxonomy"
        }.get(key, "default")
        
        self.mock_accounts_class = Mock()
        self.mock_accounts_session = Mock()
        self.mock_accounts_class.return_value = self.mock_accounts_session
        
        self.mock_data_source = Mock()
        self.mock_element = Mock()
        self.mock_data_source.get_element.return_value = self.mock_element
        
        self.mock_taxonomy = Mock()
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'ixbrl'])
    def test_ixbrl_output_format(self):
        """ixbrl output format should call to_ixbrl"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config_cls:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source_cls:
                    with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy_cls:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            with patch('sys.stdout', new_callable=StringIO):
                                
                                # Set up mocks
                                mock_config_cls.load.return_value = self.mock_config
                                mock_accounts.get_class.return_value = self.mock_accounts_class
                                mock_data_source_cls.return_value = self.mock_data_source
                                mock_taxonomy_cls.return_value = self.mock_taxonomy
                                
                                main()
                                
                                # Verify ixbrl output was called
                                self.mock_element.to_ixbrl.assert_called_once_with(self.mock_taxonomy, sys.stdout)
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_html_output_format(self):
        """html output format should call to_html"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config_cls:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source_cls:
                    with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy_cls:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            with patch('sys.stdout', new_callable=StringIO):
                                
                                # Set up mocks
                                mock_config_cls.load.return_value = self.mock_config
                                mock_accounts.get_class.return_value = self.mock_accounts_class
                                mock_data_source_cls.return_value = self.mock_data_source
                                mock_taxonomy_cls.return_value = self.mock_taxonomy
                                
                                main()
                                
                                # Verify html output was called
                                self.mock_element.to_html.assert_called_once_with(self.mock_taxonomy, sys.stdout)
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'text'])
    def test_text_output_format(self):
        """text output format should call to_text"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config_cls:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source_cls:
                    with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy_cls:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            with patch('sys.stdout', new_callable=StringIO):
                                
                                # Set up mocks
                                mock_config_cls.load.return_value = self.mock_config
                                mock_accounts.get_class.return_value = self.mock_accounts_class
                                mock_data_source_cls.return_value = self.mock_data_source
                                mock_taxonomy_cls.return_value = self.mock_taxonomy
                                
                                main()
                                
                                # Verify text output was called
                                self.mock_element.to_text.assert_called_once_with(self.mock_taxonomy, sys.stdout)
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'debug'])
    def test_debug_output_format(self):
        """debug output format should call to_debug"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config_cls:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source_cls:
                    with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy_cls:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            with patch('sys.stdout', new_callable=StringIO):
                                
                                # Set up mocks
                                mock_config_cls.load.return_value = self.mock_config
                                mock_accounts.get_class.return_value = self.mock_accounts_class
                                mock_data_source_cls.return_value = self.mock_data_source
                                mock_taxonomy_cls.return_value = self.mock_taxonomy
                                
                                main()
                                
                                # Verify debug output was called
                                self.mock_element.to_debug.assert_called_once_with(self.mock_taxonomy, sys.stdout)
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'unknown'])
    def test_unknown_output_format_raises_error(self):
        """unknown output format should raise RuntimeError"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config_cls:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source_cls:
                    with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                            
                            # Set up mocks
                            mock_config_cls.load.return_value = self.mock_config
                            mock_accounts.get_class.return_value = self.mock_accounts_class
                            mock_data_source_cls.return_value = self.mock_data_source
                            
                            with pytest.raises(RuntimeError, match="Output type 'unknown' not known"):
                                main()


class TestMainErrorHandling:
    """Test error handling and user feedback"""
    
    @patch('sys.argv', ['script', 'missing-config.yaml', 'report.yaml', 'html'])
    def test_config_load_error_handling(self):
        """Config loading errors should be caught and reported"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                
                # Simulate config loading error
                mock_config.load.side_effect = FileNotFoundError("Config file not found")
                
                with pytest.raises(FileNotFoundError):
                    main()
                
                # Verify error was written to stderr
                stderr_output = mock_stderr.getvalue()
                assert "Exception: Config file not found" in stderr_output
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_accounts_error_handling(self):
        """Accounts processing errors should be caught and reported"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                        
                        # Set up mocks
                        config_instance = Mock()
                        config_instance.get.side_effect = lambda key: {
                            "accounts.kind": "invalid",
                            "accounts.file": "test.csv"
                        }[key]
                        mock_config.load.return_value = config_instance
                        
                        # Simulate accounts error
                        mock_accounts.get_class.side_effect = RuntimeError("Invalid accounts kind")
                        
                        with pytest.raises(RuntimeError):
                            main()
                        
                        # Verify error was written to stderr
                        stderr_output = mock_stderr.getvalue()
                        assert "Exception: Invalid accounts kind" in stderr_output
    
    @patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html'])
    def test_general_exception_handling(self):
        """General exceptions should be caught, reported, and re-raised"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                
                # Simulate any exception during processing
                mock_config.load.side_effect = ValueError("Something went wrong")
                
                with pytest.raises(ValueError):
                    main()
                
                # Verify error was written to stderr
                stderr_output = mock_stderr.getvalue()
                assert "Exception: Something went wrong" in stderr_output
    
    def test_exception_details_preserved(self):
        """Exceptions should be re-raised with original details"""
        with patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html']):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('sys.stderr', new_callable=StringIO):
                    
                    # Create a specific exception
                    original_exception = ValueError("Specific error message")
                    mock_config.load.side_effect = original_exception
                    
                    # Exception should be re-raised as-is
                    with pytest.raises(ValueError) as exc_info:
                        main()
                    
                    assert str(exc_info.value) == "Specific error message"


class TestMainIntegration:
    """Integration-style tests for main() function"""
    
    @patch('sys.argv', ['ixbrl-reporter', 'config.yaml', 'report.yaml', 'html'])
    def test_complete_workflow_success(self):
        """Test complete successful workflow"""
        with patch('ixbrl_reporter.__main__.Config') as mock_config:
            with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                    with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.2.3'):
                            with patch('sys.stdout', new_callable=StringIO):
                                
                                # Set up complete mock chain
                                config_instance = Mock()
                                config_instance.get.side_effect = lambda key: {
                                    "accounts.kind": "csv",
                                    "accounts.file": "accounts.csv", 
                                    "report.taxonomy": "taxonomy.yaml"
                                }[key]
                                mock_config.load.return_value = config_instance
                                
                                accounts_class = Mock()
                                accounts_session = Mock()
                                accounts_class.return_value = accounts_session
                                mock_accounts.get_class.return_value = accounts_class
                                
                                data_source_instance = Mock()
                                element_instance = Mock()
                                data_source_instance.get_element.return_value = element_instance
                                mock_data_source.return_value = data_source_instance
                                
                                taxonomy_instance = Mock()
                                mock_taxonomy.return_value = taxonomy_instance
                                
                                # Should complete without errors
                                main()
                                
                                # Verify complete workflow
                                mock_config.load.assert_called_once_with('config.yaml')
                                config_instance.set.assert_any_call("internal.software-name", "ixbrl-reporter")
                                config_instance.set.assert_any_call("internal.software-version", "1.2.3")
                                mock_accounts.get_class.assert_called_once_with("csv")
                                accounts_class.assert_called_once_with("accounts.csv")
                                mock_data_source.assert_called_once_with(config_instance, accounts_session)
                                data_source_instance.get_element.assert_called_once_with('report.yaml')
                                mock_taxonomy.assert_called_once_with("taxonomy.yaml", data_source_instance)
                                element_instance.to_html.assert_called_once_with(taxonomy_instance, sys.stdout)


class TestMainParametrized:
    """Parametrized tests for comprehensive coverage"""
    
    @pytest.mark.parametrize("format_type,method_name", [
        ("ixbrl", "to_ixbrl"),
        ("html", "to_html"),
        ("text", "to_text"),
        ("debug", "to_debug")
    ])
    @patch('sys.stdout', new_callable=StringIO)
    def test_all_output_formats(self, mock_stdout, format_type, method_name):
        """Test that all supported output formats work correctly"""
        with patch('sys.argv', ['script', 'config.yaml', 'report.yaml', format_type]):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                    with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                        with patch('ixbrl_reporter.__main__.Taxonomy') as mock_taxonomy:
                            with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                                
                                # Set up mocks
                                config_instance = Mock()
                                config_instance.get.side_effect = lambda key: "test-value"
                                mock_config.load.return_value = config_instance
                                
                                mock_accounts.get_class.return_value = Mock(return_value=Mock())
                                
                                data_source_instance = Mock()
                                element_instance = Mock()
                                data_source_instance.get_element.return_value = element_instance
                                mock_data_source.return_value = data_source_instance
                                
                                taxonomy_instance = Mock()
                                mock_taxonomy.return_value = taxonomy_instance
                                
                                main()
                                
                                # Verify correct method was called
                                method = getattr(element_instance, method_name)
                                method.assert_called_once_with(taxonomy_instance, sys.stdout)
    
    @pytest.mark.parametrize("invalid_format", [
        "pdf", "xml", "json", "csv", "unknown", "IXBRL", "HTML"
    ])
    def test_invalid_output_formats_raise_error(self, invalid_format):
        """Test that invalid output formats raise RuntimeError"""
        with patch('sys.argv', ['script', 'config.yaml', 'report.yaml', invalid_format]):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                    with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            
                            # Set up minimal mocks
                            config_instance = Mock()
                            config_instance.get.side_effect = lambda key: "test-value"
                            mock_config.load.return_value = config_instance
                            mock_accounts.get_class.return_value = Mock(return_value=Mock())
                            mock_data_source.return_value = Mock()
                            
                            with pytest.raises(RuntimeError, match=f"Output type '{invalid_format}' not known"):
                                main()


class TestMainEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_sys_exit_unreachable_code(self):
        """Test that sys.exit(1) after raise is unreachable but doesn't break anything"""
        # This tests the unreachable sys.exit(1) after raise in the exception handler
        # The code path is unreachable but we test it doesn't cause issues
        with patch('sys.argv', ['script', 'config.yaml', 'report.yaml', 'html']):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('sys.stderr', new_callable=StringIO):
                    
                    mock_config.load.side_effect = Exception("Test error")
                    
                    # Should raise Exception, not SystemExit
                    with pytest.raises(Exception, match="Test error"):
                        main()
    
    def test_empty_string_arguments(self):
        """Test behavior with empty string arguments"""
        with patch('sys.argv', ['script', '', '', '']):
            with patch('ixbrl_reporter.__main__.Config') as mock_config:
                with patch('ixbrl_reporter.__main__.accounts') as mock_accounts:
                    with patch('ixbrl_reporter.__main__.DataSource') as mock_data_source:
                        with patch('ixbrl_reporter.__main__.version', return_value='1.1.2'):
                            
                            # Set up mocks
                            config_instance = Mock()
                            config_instance.get.side_effect = lambda key: "test"
                            mock_config.load.return_value = config_instance
                            mock_accounts.get_class.return_value = Mock(return_value=Mock())
                            mock_data_source.return_value = Mock()
                            
                            # Should attempt to process empty strings as filenames
                            # This will likely fail in Config.load, but that's expected behavior
                            try:
                                main()
                            except Exception:
                                pass  # Expected to fail, we just want to ensure no crashes